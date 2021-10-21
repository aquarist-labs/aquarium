/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { Clipboard } from '@angular/cdk/clipboard';
import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import {
  AbstractControl,
  AsyncValidatorFn,
  FormBuilder,
  FormControl,
  FormGroup,
  FormGroupDirective,
  ValidatorFn,
  Validators
} from '@angular/forms';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { Subscription } from 'rxjs';

import { bytesToSize, toBytes } from '~/app/functions.helper';
import { GlassValidators } from '~/app/shared/forms/validators';
import {
  DeclarativeForm,
  DeclarativeFormConfig,
  DeclarativeFormValues,
  FormButtonConfig,
  FormFieldConfig,
  FormFieldModifier
} from '~/app/shared/models/declarative-form-config.type';
import { ConstraintService } from '~/app/shared/services/constraint.service';
import { NotificationService } from '~/app/shared/services/notification.service';

let nextUniqueId = 0;

@Component({
  selector: 'glass-declarative-form',
  templateUrl: './declarative-form.component.html',
  styleUrls: ['./declarative-form.component.scss']
})
export class DeclarativeFormComponent implements DeclarativeForm, OnInit, OnDestroy {
  @Input()
  config?: DeclarativeFormConfig;

  @Input()
  formGroup?: FormGroup;

  private subscriptions: Subscription = new Subscription();

  constructor(
    private clipboard: Clipboard,
    private formBuilder: FormBuilder,
    private notificationService: NotificationService
  ) {}

  private static createFormControl(field: FormFieldConfig): FormControl {
    const validators: Array<ValidatorFn> = [];
    const asyncValidator: Array<AsyncValidatorFn> = [];
    if (field.validators) {
      if (_.isNumber(field.validators.min)) {
        validators.push(Validators.min(field.validators.min));
      }
      if (_.isNumber(field.validators.max)) {
        validators.push(Validators.max(field.validators.max));
      }
      if (_.isNumber(field.validators.minLength)) {
        validators.push(Validators.minLength(field.validators.minLength));
      }
      if (_.isNumber(field.validators.maxLength)) {
        validators.push(Validators.maxLength(field.validators.maxLength));
      }
      if (_.isBoolean(field.validators.required) && field.validators.required) {
        validators.push(Validators.required);
      }
      if (_.isPlainObject(field.validators.requiredIf)) {
        validators.push(GlassValidators.requiredIf(field.validators.requiredIf!));
      }
      if (_.isString(field.validators.pattern) || _.isRegExp(field.validators.pattern)) {
        validators.push(Validators.pattern(field.validators.pattern));
      }
      if (_.isString(field.validators.patternType)) {
        switch (field.validators.patternType) {
          case 'hostAddress':
            validators.push(GlassValidators.hostAddress());
            break;
        }
      }
      if (_.isPlainObject(field.validators.constraint)) {
        validators.push(
          GlassValidators.constraint(
            field.validators.constraint!.constraint,
            field.validators.constraint!.errorMessage
          )
        );
      }
      if (_.isFunction(field.validators.custom)) {
        validators.push(field.validators.custom);
      }
      if (_.isFunction(field.validators.asyncCustom)) {
        asyncValidator.push(field.validators.asyncCustom);
      }
    }
    let value = _.defaultTo(field.value, null);
    if (field.type === 'binary' && _.isNumber(value)) {
      value = bytesToSize(field.value);
    }
    return new FormControl(value, validators, asyncValidator);
  }

  ngOnInit(): void {
    this.config = _.defaultsDeep(this.config, {
      id: `glass-declarative-form-${++nextUniqueId}`
    });
    const fields: Array<FormFieldConfig> = this.getFields();
    _.forEach(fields, (field: FormFieldConfig) => {
      _.defaultsDeep(field, {
        hasCopyToClipboardButton: false,
        hasDivider: false,
        placeholder: '',
        options: {}
      });
      switch (field.type) {
        case 'checkbox':
        case 'radio':
          _.defaultsDeep(field, {
            id: `${field.name}-${++nextUniqueId}`
          });
          break;
      }
    });
    this.formGroup = this.createForm();
    // Initialize onValueChanges callbacks.
    _.forEach(
      _.filter(fields, (field) => _.isFunction(field.onValueChanges)),
      (field: FormFieldConfig) => {
        const control: AbstractControl | null = this.getControl(field.name!);
        if (control) {
          this.subscriptions.add(
            control.valueChanges.subscribe((value: any) => {
              value = this.convertToRaw(value, field);
              field.onValueChanges!(value, control, this);
            })
          );
        }
      }
    );
    // Initialize field 'modifiers' that are applied when the specified
    // constraint succeeds.
    _.forEach(
      _.filter(fields, (field) => !_.isEmpty(field.modifiers)),
      (field: FormFieldConfig) => {
        _.forEach(field.modifiers, (modifier: FormFieldModifier) => {
          const props = ConstraintService.getProps(modifier.constraint);
          _.pull(props, field.name);
          // Get notified about changes to the form fields that are
          // involved in the constraint. On value changes, test the
          // constraint and modify the target field if necessary.
          _.forEach(props, (prop: string) => {
            this.subscriptions.add(
              this.getControl(prop)?.valueChanges.subscribe(() => {
                this.applyModifier(field, modifier);
              })
            );
          });
          // Finally apply the modifier to the form field.
          this.applyModifier(field, modifier);
        });
      }
    );
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  createForm(): FormGroup {
    const controlsConfig: Record<string, FormControl> = {};
    _.forEach(this.getFields(), (field: FormFieldConfig) => {
      controlsConfig[field.name!] = DeclarativeFormComponent.createFormControl(field);
    });
    return this.formBuilder.group(controlsConfig);
  }

  getControl(path: string): AbstractControl | null {
    return this.formGroup ? this.formGroup.get(path) : null;
  }

  onCopyToClipboard(field: FormFieldConfig): void {
    const text = this.formGroup?.get(field.name!)?.value;
    const messages = {
      success: TEXT('Copied text to the clipboard successfully.'),
      error: TEXT('Failed to copy text to the clipboard.')
    };
    const success = this.clipboard.copy(text);
    this.notificationService.show(messages[success ? 'success' : 'error'], {
      type: success ? 'info' : 'error'
    });
  }

  onPaste(field: FormFieldConfig, event: ClipboardEvent): void {
    if (_.isFunction(field.onPaste)) {
      field.onPaste(event);
    }
  }

  onButtonClick(buttonConfig: FormButtonConfig) {
    if (_.isFunction(buttonConfig.click)) {
      buttonConfig.click(buttonConfig, this.values);
    }
  }

  get values(): DeclarativeFormValues {
    const values = this.formGroup?.getRawValue() ?? {};
    _.forEach(this.getFields(), (field: FormFieldConfig) => {
      const value = values[field.name!];
      if (value) {
        values[field.name!] = this.convertToRaw(value, field);
      }
    });
    return values;
  }

  get valid(): boolean {
    return this.formGroup?.valid ?? false;
  }

  patchValues(values: DeclarativeFormValues, markAsDirty: boolean = true): void {
    this.formGroup?.patchValue(values);
    if (markAsDirty) {
      _.forEach(_.keys(values), (key) => {
        const control = this.formGroup?.get(key);
        control?.markAsDirty();
      });
    }
  }

  /**
   * Reports whether the control with the given path has the error specified.
   */
  showError(
    path: Array<string | number> | string,
    fgd: FormGroupDirective,
    errorCode?: string
  ): boolean {
    const control = fgd.form.get(path);
    return control
      ? (fgd.submitted || control.dirty) &&
          (errorCode ? control.hasError(errorCode) : control.invalid)
      : false;
  }

  private getFields(): Array<FormFieldConfig> {
    const flatten = (fields: Array<FormFieldConfig>): Array<FormFieldConfig> =>
      _.flatMap(
        _.filter(
          fields,
          (field: FormFieldConfig) => !_.isUndefined(field.name) || _.isArray(field.fields)
        ),
        (field: FormFieldConfig) => {
          if (_.isArray(field.fields)) {
            return flatten(field.fields);
          } else {
            return field;
          }
        }
      );
    return flatten(this.config?.fields || []);
  }

  private convertToRaw(value: any, field: FormFieldConfig): any {
    switch (field.type) {
      case 'binary':
        value = toBytes(value);
        break;
    }
    return value;
  }

  private applyModifier(field: FormFieldConfig, modifier: FormFieldModifier) {
    const successful = ConstraintService.test(modifier.constraint, this.values);
    const opposite = _.defaultTo(modifier?.opposite, true);
    const control: AbstractControl | null = this.getControl(field.name!);
    switch (modifier.type) {
      case 'readonly':
        if (successful) {
          control?.disable();
        }
        if (!successful && opposite) {
          control?.enable();
        }
        break;
      case 'value':
        if (successful) {
          control?.setValue(modifier.data);
        }
        break;
    }
  }
}

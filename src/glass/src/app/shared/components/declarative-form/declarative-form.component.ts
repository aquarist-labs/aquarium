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
import { Component, Input, OnInit } from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  FormGroupDirective,
  ValidatorFn,
  Validators
} from '@angular/forms';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';

import { GlassValidators } from '~/app/shared/forms/validators';
import {
  DeclarativeFormConfig,
  FormButtonConfig,
  FormFieldConfig
} from '~/app/shared/models/declarative-form-config.type';
import { NotificationService } from '~/app/shared/services/notification.service';

@Component({
  selector: 'glass-declarative-form',
  templateUrl: './declarative-form.component.html',
  styleUrls: ['./declarative-form.component.scss']
})
export class DeclarativeFormComponent implements OnInit {
  @Input()
  config?: DeclarativeFormConfig;

  @Input()
  formGroup?: FormGroup;

  constructor(
    private clipboard: Clipboard,
    private formBuilder: FormBuilder,
    private notificationService: NotificationService
  ) {}

  private static createFormControl(field: FormFieldConfig): FormControl {
    const validators: Array<ValidatorFn> = [];
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
    }
    return new FormControl(_.defaultTo(field.value, null), {
      validators
    });
  }

  ngOnInit(): void {
    _.forEach(this.config?.fields, (field: FormFieldConfig) => {
      _.defaultsDeep(field, {
        hasCopyToClipboardButton: false
      });
    });
    this.formGroup = this.createForm();
  }

  createForm(): FormGroup {
    const controlsConfig: Record<string, FormControl> = {};
    _.forEach(this.config?.fields, (field: FormFieldConfig) => {
      controlsConfig[field.name] = DeclarativeFormComponent.createFormControl(field);
    });
    return this.formBuilder.group(controlsConfig);
  }

  onCopyToClipboard(field: FormFieldConfig): void {
    const text = this.formGroup?.get(field.name)?.value;
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

  get values(): Record<string, any> {
    return this.formGroup?.value ?? {};
  }

  get valid(): boolean {
    return this.formGroup?.valid ?? false;
  }

  patchValues(values: Record<string, any>): void {
    this.formGroup?.patchValue(values);
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
}

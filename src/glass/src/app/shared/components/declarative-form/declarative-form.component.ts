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
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';

import {
  DeclarativeFormConfig,
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
    return new FormControl(_.defaultTo(field.value, null));
  }

  ngOnInit(): void {
    _.forEach(this.config?.fields, (field: FormFieldConfig) => {
      switch (field.type) {
        case 'password':
          _.defaultsDeep(field, {
            hasCopyToClipboardButton: true
          });
          break;
        default:
          _.defaultsDeep(field, {
            hasCopyToClipboardButton: false
          });
          break;
      }
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

  get values(): Record<string, any> {
    return this.formGroup ? this.formGroup.value : {};
  }
}

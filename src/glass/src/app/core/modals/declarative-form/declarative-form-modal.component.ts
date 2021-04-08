import { Platform } from '@angular/cdk/platform';
import { Component, Inject } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { FormControl, ValidatorFn, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';

import {
  DeclarativeFormConfig,
  FormFieldConfig
} from '~/app/shared/models/declarative-form-config.type';
import { NotificationService } from '~/app/shared/services/notification.service';

@Component({
  selector: 'glass-declarative-form-modal',
  templateUrl: './declarative-form-modal.component.html',
  styleUrls: ['./declarative-form-modal.component.scss']
})
export class DeclarativeFormModalComponent {
  public config: DeclarativeFormConfig;
  public formGroup: FormGroup;

  constructor(
    private formBuilder: FormBuilder,
    private matDialogRef: MatDialogRef<DeclarativeFormModalComponent>,
    private platform: Platform,
    private notificationService: NotificationService,
    @Inject(MAT_DIALOG_DATA) data: DeclarativeFormConfig
  ) {
    // Sanitize the configuration.
    this.config = _.defaultsDeep(data, {
      fields: [],
      okButtonVisible: true,
      okButtonText: TEXT('OK'),
      cancelButtonVisible: true,
      cancelButtonText: TEXT('Cancel'),
      cancelButtonResult: false
    });
    _.forEach(this.config.fields, (field: FormFieldConfig) => {
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

  private static createFormControl(field: FormFieldConfig): FormControl {
    const validators: ValidatorFn[] = [];
    if (_.isBoolean(field.required) && field.required) {
      validators.push(Validators.required);
    }
    return new FormControl(_.defaultTo(field.value, null), { validators });
  }

  createForm(): FormGroup {
    const controlsConfig: Record<string, FormControl> = {};
    _.forEach(this.config.fields, (field: FormFieldConfig) => {
      controlsConfig[field.name] = DeclarativeFormModalComponent.createFormControl(field);
    });
    return this.formBuilder.group(controlsConfig);
  }

  onCopyToClipboard(field: FormFieldConfig): void {
    const text = this.formGroup.get(field.name)?.value;
    try {
      if (
        this.platform.FIREFOX ||
        this.platform.TRIDENT ||
        this.platform.IOS ||
        this.platform.SAFARI
      ) {
        // Various browsers do not support the `Permissions API`.
        // https://developer.mozilla.org/en-US/docs/Web/API/Permissions_API#Browser_compatibility
        navigator.clipboard.writeText(text).then(() => {
          this.notificationService.show(TEXT('Copied text to the clipboard successfully.'));
        });
      } else {
        // Checking if we have the clipboard-write permission
        navigator.permissions
          .query({ name: 'clipboard-write' as PermissionName })
          .then((ps: PermissionStatus) => {
            if (_.includes(['granted', 'prompt'], ps.state)) {
              navigator.clipboard.writeText(text).then(() => {
                this.notificationService.show(TEXT('Copied text to the clipboard successfully.'));
              });
            }
          });
      }
      // eslint-disable-next-line no-shadow
    } catch (_) {
      this.notificationService.show(TEXT('Failed to copy text to the clipboard.'), {
        type: 'error'
      });
    }
  }

  onOK(): void {
    const result = _.isUndefined(this.config.okButtonResult)
      ? this.formGroup.value
      : this.config.okButtonResult;
    this.matDialogRef.close(result);
  }
}

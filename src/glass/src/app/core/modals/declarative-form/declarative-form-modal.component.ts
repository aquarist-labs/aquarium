import { Component, Inject, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';

import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';
import { DeclarativeFormModalConfig } from '~/app/shared/models/declarative-form-modal-config.type';

@Component({
  selector: 'glass-declarative-form-modal',
  templateUrl: './declarative-form-modal.component.html',
  styleUrls: ['./declarative-form-modal.component.scss']
})
export class DeclarativeFormModalComponent {
  @ViewChild(DeclarativeFormComponent, { static: true })
  form!: DeclarativeFormComponent;

  public config: DeclarativeFormModalConfig;

  constructor(
    private matDialogRef: MatDialogRef<DeclarativeFormModalComponent>,
    @Inject(MAT_DIALOG_DATA) data: DeclarativeFormModalConfig
  ) {
    this.config = _.defaultsDeep(data, {
      fields: [],
      submitButtonVisible: true,
      submitButtonText: TEXT('OK'),
      submitButtonResult: undefined,
      cancelButtonVisible: true,
      cancelButtonText: TEXT('Cancel'),
      cancelButtonResult: false
    });
  }

  onOK(): void {
    const result = _.isUndefined(this.config.submitButtonResult)
      ? this.form.values
      : this.config.submitButtonResult;
    this.matDialogRef.close(result);
  }
}

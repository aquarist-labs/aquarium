import { Component, Inject, ViewChild } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import * as _ from 'lodash';

import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';
import { DeclarativeFormModalConfig } from '~/app/shared/models/declarative-form-modal-config.type';
import { GLASS_DIALOG_DATA } from '~/app/shared/services/dialog.service';

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
    public ngbActiveModal: NgbActiveModal,
    @Inject(GLASS_DIALOG_DATA) config: DeclarativeFormModalConfig
  ) {
    this.config = _.defaultsDeep(config, {
      formConfig: {
        fields: []
      },
      submitButtonVisible: true,
      submitButtonText: TEXT('OK'),
      submitButtonResult: undefined,
      cancelButtonVisible: true,
      cancelButtonText: TEXT('Cancel'),
      cancelButtonResult: false
    });
  }

  onCancel(): void {
    this.ngbActiveModal.close(this.config.cancelButtonResult);
  }

  onSubmit(): void {
    const result = _.isUndefined(this.config.submitButtonResult)
      ? this.form.values
      : this.config.submitButtonResult;
    this.ngbActiveModal.close(result);
  }
}

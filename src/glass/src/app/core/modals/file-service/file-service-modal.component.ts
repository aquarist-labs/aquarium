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
import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSliderChange } from '@angular/material/slider';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { finalize } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { GlassValidators } from '~/app/shared/forms/validators';
import {
  CheckRequirementsReply,
  Constraints,
  CreateServiceReply,
  ServicesService
} from '~/app/shared/services/api/services.service';
import { NotificationService } from '~/app/shared/services/notification.service';

@Component({
  selector: 'glass-file-service-modal',
  templateUrl: './file-service-modal.component.html',
  styleUrls: ['./file-service-modal.component.scss']
})
export class FileServiceModalComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  public formGroup: FormGroup;
  public showWarning = false;
  public showWarningText: string[] = [];
  public types = [
    {
      id: 'cephfs',
      text: 'CephFS'
    },
    {
      id: 'nfs',
      text: 'NFS'
    }
  ];
  public type: string | undefined = undefined;
  public title = 'File Service';

  private constraints: Constraints | undefined = undefined;

  constructor(
    private dialogRef: MatDialogRef<FileServiceModalComponent>,
    private services: ServicesService,
    private formBuilder: FormBuilder,
    private notification: NotificationService,
    @Inject(MAT_DIALOG_DATA) config: any
  ) {
    if (config && 'type' in config) {
      this.type = config.type;
      this.title = _.filter(this.types, ['id', config.type])[0].text;
    }
    this.formGroup = this.formBuilder.group({
      availableSpace: [0],
      reservedSpace: [0],
      rawRequiredSpace: [0],
      name: [
        '',
        [Validators.required],
        [GlassValidators.unique(this.services.exists, this.services)]
      ],
      type: [
        {
          value: this.type,
          disabled: !!this.type
        },
        [Validators.required]
      ],
      replicas: [
        2,
        [Validators.required, Validators.min(1), Validators.max(3), this.budgetValidator(this)]
      ],
      requiredSpace: [0, [Validators.required, Validators.min(1), this.budgetValidator(this)]]
    });
  }

  ngOnInit(): void {
    this.services.getConstraints().subscribe({
      next: (constraints: Constraints) => {
        this.formGroup.patchValue({
          availableSpace: _.defaultTo(constraints.allocations.available, 0),
          reservedSpace: _.defaultTo(constraints.allocations.allocated, 0)
        });
        this.constraints = constraints;
        this.updateValues();
      }
    });
  }

  public onReplicasChange(event: MatSliderChange): void {
    const replicas = !!event.value ? event.value : 0;
    this.formGroup.patchValue({ replicas });
    this.updateValues();
  }

  public onRequiredSpaceChange(event: MatSliderChange): void {
    const requiredSpace = !!event.value ? event.value : 0;
    this.formGroup.patchValue({ requiredSpace });
    this.updateValues();
  }

  public onSubmit(): void {
    if (this.formGroup.pristine || this.formGroup.invalid) {
      return;
    }
    const values = this.formGroup.value;
    this.blockUI.start(translate(TEXT('Please wait, assessing service specifications ...')));
    this.services
      .checkRequirements(values.requiredSpace, values.replicas)
      .pipe(finalize(() => this.blockUI.stop()))
      .subscribe({
        next: (result: CheckRequirementsReply) => {
          if (!result.feasible) {
            this.notification.show(translate(TEXT('Service creation requirements not met.')), {
              type: 'error'
            });
            return;
          }
          this.createService();
        },
        error: () => this.blockUI.stop()
      });
  }

  private updateValues(): void {
    const values = this.formGroup.value;
    const rawRequiredSpace = values.requiredSpace * values.replicas;
    this.formGroup.patchValue({ rawRequiredSpace });
    // Trigger the validators of the following fields.
    _.forEach(['replicas', 'requiredSpace'], (path: string) => {
      const control = this.formGroup.get(path);
      control?.updateValueAndValidity();
    });

    this.showWarning = false;
    this.showWarningText = [];
    if (this.constraints) {
      const maxReplicas = this.constraints.redundancy.max_replicas;
      const numHosts = this.constraints.availability.hosts;
      if (values.replicas > maxReplicas) {
        this.showWarning = true;
        this.showWarningText.push(
          translate(TEXT(`Current deployment can only guarantee ${maxReplicas} replicas.`))
        );
      }

      if (numHosts === 1) {
        this.showWarning = true;
        this.showWarningText.push(
          translate(TEXT('Current deployment has a single host and can\'t tolerate failures.'))
        );
      }
    }
  }

  private createService(): void {
    const values = this.formGroup.value;
    const type = values.type || this.type;
    this.blockUI.start(translate(TEXT('Please wait, deploying service ...')));
    this.services
      .create(values.name, type, values.requiredSpace, values.replicas)
      .pipe(finalize(() => this.blockUI.stop()))
      .subscribe({
        next: (result: CreateServiceReply) => {
          let success = false;
          if (!result.success) {
            this.notification.show(translate(TEXT('Failed to create service.')), { type: 'error' });
          } else {
            this.notification.show(translate(TEXT('Service successfully created.')));
            success = true;
          }
          this.dialogRef.close(success);
        }
      });
  }

  private budgetValidator(parent: any): ValidatorFn {
    return (): ValidationErrors | null => {
      if (!parent?.formGroup?.value) {
        return null;
      }
      const values = parent.formGroup.value;
      const overBudget = values.rawRequiredSpace > values.availableSpace;
      return overBudget ? { overBudget: true } : null;
    };
  }
}

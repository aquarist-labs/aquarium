import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MatSliderChange } from '@angular/material/slider';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { finalize } from 'rxjs/operators';

import {
  CheckRequirementsReply,
  Constraints,
  CreateServiceReply,
  ServicesService
} from '~/app/shared/services/api/services.service';
import { NotificationService } from '~/app/shared/services/notification.service';

@Component({
  selector: 'glass-cephfs-modal',
  templateUrl: './cephfs-modal.component.html',
  styleUrls: ['./cephfs-modal.component.scss']
})
export class CephfsModalComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  public formGroup: FormGroup;
  public showWarning = false;
  public showWarningText: string[] = [];

  private constraints: Constraints | undefined = undefined;

  public constructor(
    private dialogRef: MatDialogRef<CephfsModalComponent>,
    private services: ServicesService,
    private formBuilder: FormBuilder,
    private notification: NotificationService
  ) {
    this.formGroup = this.formBuilder.group({
      availableSpace: [0],
      reservedSpace: [0],
      rawRequiredSpace: [0],
      name: ['', [Validators.required]],
      replicas: [
        2,
        [Validators.required, Validators.min(1), Validators.max(3), this.budgetValidator(this)]
      ],
      requiredSpace: [0, [Validators.required, Validators.min(1), this.budgetValidator(this)]]
    });
  }

  public ngOnInit(): void {
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
    this.blockUI.start(TEXT('Please wait, assessing service specifications ...'));
    this.services
      .checkRequirements(values.requiredSpace, values.replicas)
      .pipe(finalize(() => this.blockUI.stop()))
      .subscribe({
        next: (result: CheckRequirementsReply) => {
          if (!result.feasible) {
            this.notification.show(TEXT('Service creation requirements not met.'), {
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

    this.showWarning = false;
    this.showWarningText = [];
    if (this.constraints) {
      const maxReplicas = this.constraints.redundancy.max_replicas;
      const numHosts = this.constraints.availability.hosts;
      if (values.replicas > maxReplicas) {
        this.showWarning = true;
        this.showWarningText.push(
          TEXT(`Current deployment can only guarantee ${maxReplicas} replicas.`)
        );
      }

      if (numHosts === 1) {
        this.showWarning = true;
        this.showWarningText.push(
          TEXT('Current deployment has a single host and can\'t tolerate failures.')
        );
      }
    }
  }

  private createService(): void {
    const values = this.formGroup.value;
    this.blockUI.start(TEXT('Please wait, deploying CephFS service ...'));
    this.services
      .create(values.name, 'cephfs', values.requiredSpace, values.replicas)
      .pipe(finalize(() => this.blockUI.stop()))
      .subscribe({
        next: (result: CreateServiceReply) => {
          let success = false;
          if (!result.success) {
            this.notification.show(TEXT('Failed to create service.'), { type: 'error' });
          } else {
            this.notification.show(TEXT('Service successfully created.'));
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

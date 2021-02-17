import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MatSliderChange } from '@angular/material/slider';
import * as _ from 'lodash';

import {
  CheckRequirementsReply,
  CreateServiceReply,
  Reservations,
  ServicesService
} from '~/app/shared/services/api/services.service';
import { NotificationService } from '~/app/shared/services/notification.service';

@Component({
  selector: 'glass-cephfs-modal',
  templateUrl: './cephfs-modal.component.html',
  styleUrls: ['./cephfs-modal.component.scss']
})
export class CephfsModalComponent implements OnInit {
  public formGroup: FormGroup;

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
      requiredSpace: [0, [Validators.required, Validators.min(0), this.budgetValidator(this)]]
    });
  }

  public ngOnInit(): void {
    this.services.reservations().subscribe({
      next: (reservations: Reservations) => {
        this.formGroup.patchValue({
          availableSpace: _.defaultTo(reservations.available, 0),
          reservedSpace: _.defaultTo(reservations.reserved, 0)
        });
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
    if (this.formGroup.invalid) {
      return;
    }
    const values = this.formGroup.value;
    this.services.checkRequirements(values.requiredSpace, values.replicas).subscribe({
      next: (result: CheckRequirementsReply) => {
        if (!result.feasible) {
          this.notification.show('Service creation requirements not met', { type: 'error' });
          return;
        }
        this.createService();
      }
    });
  }

  private updateValues(): void {
    const values = this.formGroup.value;
    const rawRequiredSpace = values.requiredSpace * values.replicas;
    this.formGroup.patchValue({ rawRequiredSpace });
  }

  private createService(): void {
    const values = this.formGroup.value;
    this.services.create(values.name, 'cephfs', values.requiredSpace, values.replicas).subscribe({
      next: (result: CreateServiceReply) => {
        let success = false;
        if (!result.success) {
          this.notification.show('Failed to create service', { type: 'error' });
        } else {
          this.notification.show('Service successfully created');
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

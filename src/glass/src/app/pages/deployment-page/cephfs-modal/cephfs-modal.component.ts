import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MatSliderChange } from '@angular/material/slider';

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
  public availableSpace = 0;
  public reservedSpace = 0;
  public rawRequiredSpace = 0;
  public replicaNumber = 2;
  public requiredSpace = 0;
  public nameFormCtrl: FormControl;

  public constructor(
    private dialogRef: MatDialogRef<CephfsModalComponent>,
    private services: ServicesService,
    private fb: FormBuilder,
    private notification: NotificationService
  ) {
    this.nameFormCtrl = this.fb.control('', Validators.required);
  }

  public ngOnInit(): void {
    this.services.reservations().subscribe({
      next: (reservations: Reservations) => {
        this.availableSpace = reservations.available;
        this.reservedSpace = reservations.reserved;
      }
    });
  }

  public onRedundancyChange(event: MatSliderChange): void {
    this.replicaNumber = !!event.value ? event.value : 0;
    this.updateRawRequiredSpace();
  }

  public onSpaceChange(event: MatSliderChange): void {
    this.requiredSpace = !!event.value ? event.value : 0;
    this.updateRawRequiredSpace();
  }

  public sliderDisplayValue(input: number): string {
    return `${input} replicas`;
  }

  public onCancel(): void {
    this.dialogRef.close(false);
  }

  public onSubmit(): void {
    if (
      !this.nameFormCtrl.valid ||
      this.requiredSpace === 0 ||
      this.rawRequiredSpace > this.availableSpace
    ) {
      return;
    }

    this.services.checkRequirements(this.requiredSpace, this.replicaNumber).subscribe({
      next: (result: CheckRequirementsReply) => {
        if (!result.feasible) {
          this.notification.show('Service Creation requirements not met', { type: 'error' });
          return;
        }
        this.createService();
      }
    });
  }

  public isValid(): boolean {
    return this.nameFormCtrl.valid && this.requiredSpace > 0 && !this.isOverBudget();
  }

  public isOverBudget(): boolean {
    return this.rawRequiredSpace > this.availableSpace;
  }

  private updateRawRequiredSpace(): void {
    this.rawRequiredSpace = this.requiredSpace * this.replicaNumber;
  }

  private createService(): void {
    const name: string = this.nameFormCtrl.value as string;
    this.services.create(name, 'cephfs', this.requiredSpace, this.replicaNumber).subscribe({
      next: (result: CreateServiceReply) => {
        let success = false;
        if (!result.success) {
          this.notification.show('Error creating Service', { type: 'error' });
        } else {
          this.notification.show('Service created', { type: 'info' });
          success = true;
        }
        this.dialogRef.close(success);
      }
    });
  }
}

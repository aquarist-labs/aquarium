import { Component, OnInit, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatStepper } from '@angular/material/stepper';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { of } from 'rxjs';
import { delay, mergeMap } from 'rxjs/operators';

import { ChooseDevicesModalComponent } from '~/app/pages/deployment-page/choose-devices-modal/choose-devices-modal.component';
import { Device, OrchService } from '~/app/shared/services/api/orch.service';
import { NotificationService } from '~/app/shared/services/notification.service';

@Component({
  selector: 'glass-deployment-page',
  templateUrl: './deployment-page.component.html',
  styleUrls: ['./deployment-page.component.scss']
})
export class DeploymentPageComponent implements OnInit {
  @ViewChild(MatStepper)
  set stepper(s: MatStepper) {
    this.deploymentStepper = s;
  }

  @BlockUI()
  blockUI!: NgBlockUI;

  nfs = false;
  devices: Device[] = [];
  deploymentStepper!: MatStepper;
  displayInventory = true;
  deploymentSuccessful = false;

  constructor(
    private dialog: MatDialog,
    private notificationService: NotificationService,
    private orchService: OrchService
  ) {}

  ngOnInit(): void {
    this.getDevices();
  }

  addNfs(): void {
    this.nfs = true;
  }

  getDevices(): void {
    this.orchService.devices().subscribe((hostDevices) => {
      Object.values(hostDevices).forEach((v) => {
        this.devices = this.devices.concat(v.devices);
      });
    });
  }

  chooseDevices(): void {
    const dialogRef = this.dialog.open(ChooseDevicesModalComponent, {
      width: '50%'
    });
    dialogRef.afterClosed().subscribe((decision: boolean) => {
      dialogRef.close();

      if (decision) {
        this.startAssimilation();
      }
    });
  }

  startAssimilation(): void {
    this.displayInventory = false;
    this.blockUI.start('Please wait, disk deployment in progress ...');
    this.orchService.assimilateDevices().subscribe(
      (success) => {
        if (success) {
          this.pollAssimilationStatus();
        } else {
          this.displayInventory = true;
          this.blockUI.stop();
          this.notificationService.show('Failed to start disk deployment.', {
            type: 'error'
          });
        }
      },
      () => {
        this.displayInventory = true;
        this.blockUI.stop();
      }
    );
  }

  pollAssimilationStatus(): void {
    const handleError = (err?: any) => {
      this.displayInventory = true;
      this.blockUI.stop();
      this.notificationService.show('Failed to deploy disks.', {
        type: 'error'
      });
    };
    of(true)
      .pipe(
        delay(5000),
        mergeMap(() => this.orchService.assimilateStatus())
      )
      .subscribe(
        (success) => {
          if (success) {
            this.displayInventory = true;
            this.deploymentStepper.next();
            this.blockUI.stop();
          } else {
            this.pollAssimilationStatus();
          }
        },
        (err) => {
          handleError(err);
        }
      );
  }
}

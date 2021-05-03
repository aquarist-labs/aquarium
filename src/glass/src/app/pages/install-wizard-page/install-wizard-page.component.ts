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
import { Component, OnInit, ViewChild } from '@angular/core';
import { MatStepper } from '@angular/material/stepper';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { forkJoin } from 'rxjs';
import { tap } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { InstallWizardContext } from '~/app/pages/install-wizard-page/models/install-wizard-context.type';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import {
  BootstrapBasicReply,
  BootstrapService,
  BootstrapStageEnum,
  BootstrapStatusReply
} from '~/app/shared/services/api/bootstrap.service';
import { StatusStageEnum } from '~/app/shared/services/api/local.service';
import { LocalNodeService, NodeStatus } from '~/app/shared/services/api/local.service';
import { OrchService } from '~/app/shared/services/api/orch.service';
import { DialogService } from '~/app/shared/services/dialog.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

@Component({
  selector: 'glass-install-wizard-page',
  templateUrl: './install-wizard-page.component.html',
  styleUrls: ['./install-wizard-page.component.scss']
})
export class InstallWizardPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  @ViewChild(MatStepper, { static: false })
  stepper?: MatStepper;

  public context: InstallWizardContext = {
    config: {},
    stage: 'unknown',
    stepperVisible: true
  };
  public pageIndex = {
    start: 0,
    networking: 1,
    installation: 2,
    devices: 3,
    services: 4,
    summary: 5
  };

  constructor(
    private bootstrapService: BootstrapService,
    private dialogService: DialogService,
    private localNodeService: LocalNodeService,
    private notificationService: NotificationService,
    private orchService: OrchService,
    private pollService: PollService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.blockUI.start(translate(TEXT(`Please wait, checking system status ...`)));
    forkJoin({
      bootstrapStatusReply: this.bootstrapService.status(),
      nodeStatus: this.localNodeService.status()
    }).subscribe({
      next: (res) => {
        this.blockUI.stop();
        switch (res.nodeStatus.node_stage) {
          case StatusStageEnum.bootstrapped:
            this.context.stage = 'bootstrapped';
            this.context.stepperVisible = true;
            // Jump to the 'Devices' step.
            this.stepper!.selectedIndex = this.pageIndex.devices;
            break;
          case StatusStageEnum.ready:
            this.context.stage = 'deployed';
            this.context.stepperVisible = true;
            // Jump to the 'Services' step.
            this.stepper!.selectedIndex = this.pageIndex.services;
            break;
          default:
            switch (res.bootstrapStatusReply.stage) {
              case BootstrapStageEnum.running:
                this.context.stage = 'bootstrapping';
                this.context.stepperVisible = true;
                // Jump to the 'Installation' step.
                this.stepper!.selectedIndex = this.pageIndex.installation;
                // Immediately show the progress message.
                this.blockUI.start(
                  translate(
                    TEXT(
                      `Please wait, bootstrapping in progress (${res.bootstrapStatusReply.progress}%) ...`
                    )
                  )
                );
                this.pollBootstrapStatus();
                break;
              case BootstrapStageEnum.done:
                this.context.stage = 'bootstrapped';
                this.context.stepperVisible = true;
                // Jump to the 'Devices' step.
                this.stepper!.selectedIndex = this.pageIndex.devices;
                break;
              case BootstrapStageEnum.none:
                // Force linear mode.
                this.stepper!.linear = true;
                break;
            }
        }
      },
      error: (err) => this.handleError(err)
    });
  }

  /**
   * This step contains the following steps:
   * - Configure NTP
   * - Start bootstrap process
   */
  startBootstrap(): void {
    this.orchService.setNtp(this.context.config.ntpAddress).subscribe(
      () => {
        this.blockUI.start(translate(TEXT('Please wait, checking node status ...')));
        this.pollNodeStatus();
      },
      (err) => this.handleError(err.message)
    );
  }

  startDeviceDeployment(): void {
    this.dialogService.open(
      DialogComponent,
      (decision) => {
        if (decision) {
          this.blockUI.start(translate(TEXT('Please wait, device deployment in progress ...')));
          this.orchService.assimilateDevices().subscribe(
            (success) => {
              if (success) {
                this.pollDeviceDeploymentStatus();
              } else {
                this.handleError(TEXT('Failed to start device deployment.'));
              }
            },
            (err) => this.handleError(err)
          );
        }
      },
      {
        width: '35%',
        data: {
          type: 'yesNo',
          icon: 'warn',
          title: TEXT('Deploy devices'),
          message: TEXT(
            'This step will erase all data on the listed devices. Are you sure you want to continue?'
          )
        }
      }
    );
  }

  finishDeployment(): void {
    this.blockUI.start(translate(TEXT("Finishing deployment ...")));
    this.bootstrapService.markFinished().subscribe({
      next: () => {
        this.blockUI.stop();
        this.router.navigate(["/dashboard"]);
      }
    });
  }

  private handleError(err: any): void {
    this.context.stepperVisible = true;
    this.blockUI.stop();
    this.notificationService.show(err.toString(), {
      type: 'error'
    });
  }

  private pollNodeStatus(): void {
    this.localNodeService
      .status()
      .pipe(
        this.pollService.poll(
          (status: NodeStatus) => !status.inited,
          10,
          TEXT('Bootstrapping not possible at the moment, please retry later.'),
          1000
        )
      )
      .subscribe(
        (status: NodeStatus) => {
          this.blockUI.stop();
          if (status.inited) {
            this.doBootstrap();
          }
        },
        (err) => this.handleError(err.message)
      );
  }

  private doBootstrap(): void {
    this.context.stepperVisible = false;
    this.blockUI.start(translate(TEXT('Please wait, bootstrapping will be started ...')));
    this.bootstrapService.start().subscribe({
      next: (basicReplay: BootstrapBasicReply) => {
        if (basicReplay.success) {
          this.context.stage = 'bootstrapping';
          this.blockUI.update(translate(TEXT('Please wait, bootstrapping in progress ...')));
          this.pollBootstrapStatus();
        } else {
          this.context.stepperVisible = true;
          this.blockUI.stop();
          this.notificationService.show(TEXT('Failed to start bootstrapping the system.'), {
            type: 'error'
          });
        }
      },
      error: (err) => this.handleError(err)
    });
  }

  private pollBootstrapStatus(): void {
    this.context.stepperVisible = false;
    this.bootstrapService
      .status()
      .pipe(
        tap((statusReply: BootstrapStatusReply) => {
          this.blockUI.update(
            translate(TEXT(`Please wait, bootstrapping in progress (${statusReply.progress}%) ...`))
          );
        }),
        this.pollService.poll(
          (statusReply) => statusReply.stage === BootstrapStageEnum.running,
          Infinity,
          TEXT('Failed to bootstrap the system.')
        )
      )
      .subscribe(
        (statusReply: BootstrapStatusReply) => {
          switch (statusReply.stage) {
            case BootstrapStageEnum.error:
              this.handleError(TEXT('Failed to bootstrap the system.'));
              break;
            case BootstrapStageEnum.none:
            case BootstrapStageEnum.done:
              this.blockUI.update(
                translate(
                  TEXT(`Please wait, bootstrapping in progress (${statusReply.progress}%) ...`)
                )
              );
              this.context.stage = 'bootstrapped';
              this.context.stepperVisible = true;
              this.blockUI.stop();
              this.stepper!.next();
              break;
          }
        },
        () => this.handleError(TEXT('Failed to bootstrap the system.'))
      );
  }

  private pollDeviceDeploymentStatus(): void {
    this.context.stepperVisible = false;
    this.orchService
      .assimilateStatus()
      .pipe(this.pollService.poll((res) => !res, undefined, 'Failed to deploy devices.'))
      .subscribe(
        (res) => {
          this.context.stage = 'deployed';
          this.context.stepperVisible = true;
          this.blockUI.stop();
          this.stepper?.next();
        },
        (err) => this.handleError(err)
      );
  }
}

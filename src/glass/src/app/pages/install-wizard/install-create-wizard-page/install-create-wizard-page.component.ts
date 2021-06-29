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
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { forkJoin } from 'rxjs';
import { tap } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { InstallWizardContext } from '~/app/pages/install-wizard/models/install-wizard-context.type';
import { StatusStageEnum } from '~/app/shared/services/api/local.service';
import { LocalNodeService, NodeStatus } from '~/app/shared/services/api/local.service';
import {
  DeploymentStartReply,
  DeploymentStatusReply,
  NodesService,
  NodeStageEnum
} from '~/app/shared/services/api/nodes.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

type InstallCreateWizardContext = InstallWizardContext & {
  stage: 'unknown' | 'bootstrapping' | 'bootstrapped' | 'deployed';
};

@Component({
  selector: 'glass-install-create-wizard-page',
  templateUrl: './install-create-wizard-page.component.html',
  styleUrls: ['./install-create-wizard-page.component.scss']
})
export class InstallCreateWizardPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  @ViewChild(MatStepper, { static: false })
  stepper?: MatStepper;

  public context: InstallCreateWizardContext = {
    config: {},
    stage: 'unknown',
    stepperVisible: false
  };
  public pageIndex = {
    start: 0,
    hostname: 1,
    ntp: 2,
    localDevices: 3,
    installation: 4,
    services: 5,
    finish: 6
  };

  constructor(
    private localNodeService: LocalNodeService,
    private nodesService: NodesService,
    private notificationService: NotificationService,
    private pollService: PollService
  ) {}

  ngOnInit(): void {
    this.blockUI.start(translate(TEXT(`Please wait, checking system status ...`)));
    forkJoin({
      deploymentStatusReply: this.nodesService.deploymentStatus(),
      nodeStatus: this.localNodeService.status()
    }).subscribe({
      next: (res) => {
        this.blockUI.stop();
        switch (res.nodeStatus.node_stage) {
          case StatusStageEnum.bootstrapped:
            this.context.stage = 'bootstrapped';
            this.context.stepperVisible = true;
            // Jump to the 'Services' step.
            this.stepper!.selectedIndex = this.pageIndex.services;
            break;
          case StatusStageEnum.ready:
            this.context.stage = 'deployed';
            this.context.stepperVisible = true;
            // Jump to the 'Services' step.
            this.stepper!.selectedIndex = this.pageIndex.services;
            break;
          default:
            this.context.stepperVisible = true;
            switch (res.deploymentStatusReply.stage) {
              case NodeStageEnum.bootstrapping:
                this.context.stage = 'bootstrapping';
                // Jump to the 'Installation' step.
                this.stepper!.selectedIndex = this.pageIndex.installation;
                // Immediately show the progress message.
                this.blockUI.start(
                  translate(
                    TEXT(
                      `Please wait, deployment in progress (${res.deploymentStatusReply.progress}%) ...`
                    )
                  )
                );
                this.pollBootstrapStatus();
                break;
              case NodeStageEnum.deployed:
                this.context.stage = 'bootstrapped';
                // Jump to the 'Services' step.
                this.stepper!.selectedIndex = this.pageIndex.services;
                break;
              case NodeStageEnum.none:
                // Force linear mode.
                this.stepper!.linear = true;
                break;
            }
        }
      },
      error: (err) => {
        err.preventDefault();
        this.stepper!.linear = true;
        this.handleError(err.message);
      }
    });
  }

  onAnimationDone(): void {
    // Focus the first element with the 'autofocus' attribute.
    if (this.stepper) {
      // eslint-disable-next-line no-underscore-dangle
      const stepContentId = this.stepper._getStepContentId(this.stepper.selectedIndex);
      const stepContentElement = document.getElementById(stepContentId);
      const element: HTMLElement | null | undefined = stepContentElement?.querySelector(
        '[ng-reflect-autofocus=true]'
      );
      if (element && _.isFunction(element.focus)) {
        element.focus();
      }
    }
  }

  /**
   * This step starts the bootstrap process
   */
  startBootstrap(): void {
    this.blockUI.start(translate(TEXT('Please wait, checking node status ...')));
    this.pollNodeStatus();
  }

  finishDeployment(): void {
    this.context.stepperVisible = false;
    this.blockUI.start(translate(TEXT(`Please wait, finishing deployment ...`)));
    this.nodesService.markDeploymentFinished().subscribe(
      (success: boolean) => {
        this.blockUI.stop();
        this.context.stepperVisible = true;
        if (success) {
          this.stepper!.next();
        } else {
          this.handleError(TEXT('Unable to finish deployment.'));
        }
      },
      (err) => {
        err.preventDefault();
        this.handleError(err.message);
      }
    );
  }

  private handleError(message: string): void {
    this.context.stepperVisible = true;
    this.blockUI.stop();
    this.notificationService.show(message, {
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
        (err) => {
          err.preventDefault();
          this.handleError(err.message);
        }
      );
  }

  private doBootstrap(): void {
    this.context.stepperVisible = false;
    this.blockUI.start(translate(TEXT('Please wait, bootstrapping will be started ...')));
    this.nodesService
      .deploymentStart({
        ntpaddr: this.context.config.ntpAddress,
        hostname: this.context.config.hostname
      })
      .subscribe({
        next: (startReplay: DeploymentStartReply) => {
          if (startReplay.success) {
            this.context.stage = 'bootstrapping';
            this.blockUI.update(translate(TEXT('Please wait, bootstrapping in progress ...')));
            this.pollBootstrapStatus();
          } else {
            this.handleError(
              TEXT(`Failed to start bootstrapping the system: ${startReplay.error.message}`)
            );
          }
        },
        error: (err) => {
          err.preventDefault();
          this.handleError(err.message);
        }
      });
  }

  private pollBootstrapStatus(): void {
    this.context.stepperVisible = false;
    this.nodesService
      .deploymentStatus()
      .pipe(
        tap((statusReply: DeploymentStatusReply) => {
          this.blockUI.update(
            translate(TEXT(`Please wait, bootstrapping in progress (${statusReply.progress}%) ...`))
          );
        }),
        this.pollService.poll(
          (statusReply) => statusReply.stage === NodeStageEnum.bootstrapping,
          Infinity,
          TEXT('Failed to bootstrap the system.')
        )
      )
      .subscribe(
        (statusReply: DeploymentStatusReply) => {
          switch (statusReply.stage) {
            case NodeStageEnum.error:
              this.handleError(TEXT('Failed to bootstrap the system.'));
              break;
            case NodeStageEnum.none:
            case NodeStageEnum.deployed:
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
        (err) => {
          err.preventDefault();
          this.handleError(TEXT('Failed to bootstrap the system.'));
        }
      );
  }
}

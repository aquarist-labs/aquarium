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
import { Component, OnInit } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { translate } from '~/app/i18n.helper';
import { InstallWizardContext } from '~/app/pages/install-wizard/models/install-wizard-context.type';
import { Icon } from '~/app/shared/enum/icon.enum';
import {
  DeployCreateParams,
  DeploymentStateEnum,
  DeployService,
  DeployStatusReply,
  InitStateEnum,
  Progress
} from '~/app/shared/services/api/deploy.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

@Component({
  selector: 'glass-install-create-wizard-page',
  templateUrl: './install-create-wizard-page.component.html',
  styleUrls: ['./install-create-wizard-page.component.scss']
})
export class InstallCreateWizardPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  public icons = Icon;
  public activeId = 1;
  public context: InstallWizardContext = {
    config: {}
  };
  public pageIndex = {
    start: 1,
    networking: 2,
    time: 3,
    devices: 4,
    deployment: 5,
    finish: 6
  };
  public deployed = false;
  public error: boolean | string = false;

  constructor(
    private deployService: DeployService,
    private notificationService: NotificationService,
    private pollService: PollService
  ) {}

  ngOnInit(): void {
    this.startProgress(TEXT(`Please wait, checking system status ...`));
    this.deployService.status().subscribe({
      next: (res: DeployStatusReply) => {
        this.stopProgress();
        switch (res.status.state.init) {
          case InitStateEnum.deployed:
            this.deployed = true;
            this.activeId = this.pageIndex.finish;
            break;
          default:
            switch (res.status.state.deployment) {
              case DeploymentStateEnum.none:
                this.deployed = false;
                this.activeId = this.pageIndex.start;
                break;
              case DeploymentStateEnum.deploying:
                this.deployed = false;
                this.activeId = this.pageIndex.deployment;
                this.startProgress();
                this.pollStatus();
                break;
              case DeploymentStateEnum.deployed:
                this.deployed = true;
                this.activeId = this.pageIndex.finish;
                break;
              case DeploymentStateEnum.error:
                this.handleError(res.status.error.msg!, true);
                break;
            }
        }
      },
      error: (err) => {
        err.preventDefault();
        this.handleError(err.message);
      }
    });
  }

  onInstall(): void {
    this.doDeployment();
  }

  private doDeployment(): void {
    const params: DeployCreateParams = {
      ntpaddr: this.context.config.ntpAddress,
      hostname: this.context.config.hostname,
      storage: this.context.config.storage
    };
    if (!this.context.config.regDefault) {
      params.registry = {
        registry: this.context.config.registry,
        image: this.context.config.image,
        secure: this.context.config.secure
      };
    }
    this.deployService.create(params).subscribe({
      next: (res: DeployStatusReply) => {
        // Is there an error?
        if (_.isString(res.status.error.msg) && !_.isEmpty(res.status.error.msg)) {
          this.handleError(res.status.error.msg, true);
        } else {
          this.startProgress();
          this.pollStatus();
        }
      },
      error: (err) => {
        err.preventDefault();
        this.handleError(err.message);
      }
    });
  }

  private pollStatus(): void {
    this.deployService
      .status()
      .pipe(
        this.pollService.poll((res: DeployStatusReply) => {
          // Is there an error?
          if (_.isString(res.status.error.msg) && !_.isEmpty(res.status.error.msg)) {
            this.handleError(res.status.error.msg, true);
            return false;
          }
          this.updateProgress(res.status.progress);
          return res.status.state.deployment === DeploymentStateEnum.deploying;
        })
      )
      .subscribe(
        (res: DeployStatusReply) => {
          this.stopProgress();
          switch (res.status.state.init) {
            case InitStateEnum.deployed:
              this.deployed = true;
              this.activeId = this.pageIndex.finish;
              break;
            default:
              // Nothing to do here.
              break;
          }
        },
        (err) => {
          err.preventDefault();
          this.handleError(TEXT('Failed to deploy the system.'));
        }
      );
  }

  private startProgress(text?: string): void {
    if (!_.isString(text)) {
      text = TEXT('Please wait, deployment in progress ...');
    }
    this.blockUI.start(translate(text));
  }

  private updateProgress(progress?: Progress): void {
    if (_.isNull(progress) || _.isUndefined(progress)) {
      this.blockUI.update(translate(TEXT('Please wait, deployment in progress ...')));
    } else {
      this.blockUI.update(
        translate(TEXT(`Please wait, deployment in progress (${progress.value}%) ...`))
      );
    }
  }

  private stopProgress(): void {
    this.blockUI.stop();
  }

  private handleError(message: string, failHard = false): void {
    this.stopProgress();
    if (failHard) {
      this.error = message;
    } else {
      this.notificationService.show(message, {
        type: 'error'
      });
    }
  }
}

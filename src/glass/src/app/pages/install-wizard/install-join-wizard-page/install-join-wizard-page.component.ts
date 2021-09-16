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
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { translate } from '~/app/i18n.helper';
import { InstallWizardContext } from '~/app/pages/install-wizard/models/install-wizard-context.type';
import { Icon } from '~/app/shared/enum/icon.enum';
import {
  LocalNodeService,
  NodeStatus,
  StatusStageEnum
} from '~/app/shared/services/api/local.service';
import { NodesService } from '~/app/shared/services/api/nodes.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

type InstallJoinWizardContext = InstallWizardContext & {
  stage: 'unknown' | 'joining' | 'joined';
};

@Component({
  selector: 'glass-install-join-wizard-page',
  templateUrl: './install-join-wizard-page.component.html',
  styleUrls: ['./install-join-wizard-page.component.scss']
})
export class InstallJoinWizardPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  public icons = Icon;
  public activeId = 1;
  public context: InstallJoinWizardContext = {
    config: {},
    stage: 'unknown'
  };
  public pageIndex = {
    start: 1,
    networking: 2,
    devices: 3,
    registration: 4,
    join: 5,
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
    this.localNodeService.status().subscribe(
      (res: NodeStatus) => {
        this.blockUI.stop();
        switch (res.node_stage) {
          case StatusStageEnum.joining:
            this.context.stage = 'joining';
            // Jump to the 'Summary' step.
            this.activeId = this.pageIndex.join;
            // Immediately show the progress message.
            this.blockUI.start(
              translate(TEXT('Please wait, joining existing cluster in progress ...'))
            );
            this.pollJoiningStatus();
            break;
          case StatusStageEnum.ready:
            this.context.stage = 'joined';
            // Jump to the 'Finish' step.
            this.activeId = this.pageIndex.finish;
            break;
          default:
            break;
        }
      },
      (err) => this.handleError(err.message)
    );
  }

  doJoin(): void {
    this.context.stage = 'joining';
    this.blockUI.start(translate(TEXT('Please wait, start joining existing cluster ...')));
    this.nodesService
      .join({
        address: `${this.context.config.address}:${this.context.config.port}`,
        token: this.context.config.token,
        hostname: this.context.config.hostname
      })
      .subscribe({
        next: (success: boolean) => {
          if (success) {
            this.blockUI.update(
              translate(TEXT('Please wait, joining existing cluster in progress ...'))
            );
            this.pollJoiningStatus();
          } else {
            this.handleError(TEXT('Failed to join existing cluster.'));
          }
        },
        error: (err) => this.handleError(err.message)
      });
  }

  private handleError(err: any): void {
    this.blockUI.stop();
    this.notificationService.show(err.toString(), {
      type: 'error'
    });
  }

  private pollJoiningStatus(): void {
    this.localNodeService
      .status()
      .pipe(
        this.pollService.poll(
          (res: NodeStatus) => res.node_stage === StatusStageEnum.joining,
          undefined,
          TEXT('Failed to join existing cluster.')
        )
      )
      .subscribe(
        (res: NodeStatus) => {
          switch (res.node_stage) {
            case StatusStageEnum.none:
            case StatusStageEnum.unknown:
              this.context.stage = 'unknown';
              this.handleError(TEXT('Failed to join existing cluster.'));
              break;
            case StatusStageEnum.ready:
              this.context.stage = 'joined';
              this.blockUI.stop();
              this.activeId++;
              break;
          }
        },
        (err) => this.handleError(err.message)
      );
  }
}

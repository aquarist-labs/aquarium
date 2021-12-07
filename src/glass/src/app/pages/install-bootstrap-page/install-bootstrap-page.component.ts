import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { translate } from '~/app/i18n.helper';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import {
  DeployDevicesReply,
  DeploymentStateEnum,
  DeploymentStatus,
  DeployService,
  DeployStatusReply,
  Progress
} from '~/app/shared/services/api/deploy.service';
import { Disk } from '~/app/shared/services/api/local.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

@Component({
  selector: 'glass-install-bootstrap-page',
  templateUrl: './install-bootstrap-page.component.html',
  styleUrls: ['./install-bootstrap-page.component.scss']
})
export class InstallBootstrapPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  public bootstrapping = false;
  public devices: Disk[] = [];
  public devicesColumns: DatatableColumn[] = [
    {
      name: TEXT('Path'),
      prop: 'path'
    },
    {
      name: TEXT('Type'),
      prop: 'rotational',
      cellTemplateName: DatatableCellTemplateName.badge,
      cellTemplateConfig: {
        map: {
          true: { value: TEXT('HDD'), class: 'glass-color-theme-gray-600' },
          false: { value: TEXT('NVMe/SSD'), class: 'glass-color-theme-yellow-500' }
        }
      }
    },
    {
      name: TEXT('Product'),
      prop: 'product'
    },
    {
      name: TEXT('Vendor'),
      prop: 'vendor'
    },
    {
      name: TEXT('Size'),
      prop: 'size',
      pipe: new BytesToSizePipe()
    }
  ];
  public targetDevice?: string;
  public error: boolean | string = false;

  constructor(
    private deployService: DeployService,
    private notificationService: NotificationService,
    private pollService: PollService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.startProgress(TEXT(`Please wait, checking system status ...`));
    this.deployService.status().subscribe(
      (dsr: DeployStatusReply) => {
        this.stopProgress();
        switch (dsr.status.state.deployment) {
          case DeploymentStateEnum.none:
            this.deployService.devices().subscribe((ddr: DeployDevicesReply) => {
              if (!ddr.devices.length) {
                this.handleError(TEXT('No storage devices found.'), true);
              } else {
                this.devices = ddr.devices;
              }
            });
            break;
          case DeploymentStateEnum.installing:
            this.continueBootstrapping(dsr.status);
            break;
          case DeploymentStateEnum.error:
            this.handleError(dsr.status.error.msg!, true);
            break;
          default:
            break;
        }
      },
      (err) => {
        err.preventDefault();
        this.handleError(err.message);
      }
    );
  }

  onSelectionChange(selection: DatatableData[]): void {
    if (selection.length === 1) {
      this.targetDevice = _.get(selection[0], 'path');
    } else {
      this.targetDevice = undefined;
    }
  }

  onInstall(): void {
    this.doBootstrapping();
  }

  private doBootstrapping(): void {
    this.deployService
      .install({
        device: this.targetDevice as string
      })
      .subscribe(
        () => {
          this.bootstrapping = true;
          this.startProgress();
          this.pollStatus();
        },
        (err) => {
          err.preventDefault();
          this.handleError(err.message);
        }
      );
  }

  private continueBootstrapping(status: DeploymentStatus): void {
    this.bootstrapping = true;
    this.startProgress();
    this.updateProgress(status.progress);
    this.pollStatus();
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
          // Was bootstrapping successful?
          if (res.installed) {
            return false;
          }
          this.updateProgress(res.status.progress);
          return res.status.state.deployment === DeploymentStateEnum.installing;
        })
      )
      .subscribe(
        (res: DeployStatusReply) => {
          this.stopProgress();
          if (res.installed) {
            this.router.navigate(['/installer/install-mode']);
          }
        },
        (err) => {
          err.preventDefault();
          this.handleError(TEXT('Failed to bootstrap the system.'));
        }
      );
  }

  private startProgress(text?: string): void {
    if (!_.isString(text)) {
      text = TEXT('Please wait, bootstrapping in progress ...');
    }
    this.blockUI.start(translate(text));
  }

  private updateProgress(progress?: Progress): void {
    if (_.isNull(progress) || _.isUndefined(progress)) {
      this.blockUI.update(translate(TEXT('Please wait, bootstrapping in progress ...')));
    } else {
      this.blockUI.update(
        translate(TEXT(`Please wait, bootstrapping in progress (${progress.value}%) ...`))
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

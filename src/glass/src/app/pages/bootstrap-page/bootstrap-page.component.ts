import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { translate } from '~/app/i18n.helper';
import {
  BootstrapBasicReply,
  BootstrapService,
  BootstrapStageEnum,
  BootstrapStatusReply
} from '~/app/shared/services/api/bootstrap.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

@Component({
  selector: 'glass-bootstrap-page',
  templateUrl: './bootstrap-page.component.html',
  styleUrls: ['./bootstrap-page.component.scss']
})
export class BootstrapPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  bootstrapping = false;

  constructor(
    private bootstrapService: BootstrapService,
    private notificationService: NotificationService,
    private router: Router,
    private pollService: PollService
  ) {}

  ngOnInit(): void {
    this.blockUI.resetGlobal();
    // Immediately block the UI if bootstrapping is in progress.
    this.bootstrapService.status().subscribe({
      next: (statusReply: BootstrapStatusReply) => {
        if (statusReply.stage === BootstrapStageEnum.running) {
          this.bootstrapping = true;
          this.blockUI.start(translate(TEXT('Please wait, bootstrapping in progress ...')));
          this.pollBootstrapStatus();
        }
        if (statusReply.stage === BootstrapStageEnum.none) {
          this.bootstrapping = false;
        }
      },
      error: () => (this.bootstrapping = false)
    });
  }

  doBootstrap(): void {
    this.bootstrapping = true;
    this.blockUI.start(translate(TEXT('Please wait, bootstrapping will be started ...')));
    this.bootstrapService.start().subscribe({
      next: (basicReplay: BootstrapBasicReply) => {
        if (basicReplay.success) {
          this.blockUI.update(translate(TEXT('Please wait, bootstrapping in progress ...')));
          this.pollBootstrapStatus();
        } else {
          this.bootstrapping = false;
          this.blockUI.stop();
          this.notificationService.show(TEXT('Failed to start bootstrapping the system.'), {
            type: 'error'
          });
        }
      },
      error: () => {
        this.bootstrapping = false;
        this.blockUI.stop();
      }
    });
  }

  pollBootstrapStatus(): void {
    const handleError = () => {
      this.bootstrapping = false;
      this.blockUI.stop();
      this.notificationService.show(TEXT('Failed to bootstrap the system.'), {
        type: 'error'
      });
    };
    this.bootstrapService
      .status()
      .pipe(
        this.pollService.poll(
          (statusReply) => statusReply.stage === BootstrapStageEnum.running,
          undefined,
          TEXT('Failed to bootstrap the system.')
        )
      )
      .subscribe(
        (statusReply: BootstrapStatusReply) => {
          switch (statusReply.stage) {
            case BootstrapStageEnum.error:
              handleError();
              break;
            case BootstrapStageEnum.none:
            case BootstrapStageEnum.done:
              this.blockUI.stop();
              this.router.navigate(['/installer/create/deployment']);
              break;
          }
        },
        () => handleError()
      );
  }
}

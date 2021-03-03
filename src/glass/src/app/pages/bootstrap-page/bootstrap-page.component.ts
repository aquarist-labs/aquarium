import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

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

  visible = false;

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
          this.visible = false;
          this.blockUI.start('Please wait, bootstrapping in progress ...');
          this.pollBootstrapStatus();
        }
        if (statusReply.stage === BootstrapStageEnum.none) {
          this.visible = true;
        }
      },
      error: () => (this.visible = true)
    });
  }

  startBootstrap(): void {
    this.visible = false;
    this.blockUI.start('Please wait, bootstrapping will be started ...');

    this.bootstrapService.start().subscribe({
      next: (basicReplay: BootstrapBasicReply) => {
        if (basicReplay.success) {
          this.blockUI.update('Please wait, bootstrapping in progress ...');
          this.pollBootstrapStatus();
        } else {
          this.visible = true;
          this.blockUI.stop();
          this.notificationService.show('Failed to start bootstrapping the system.', {
            type: 'error'
          });
        }
      },
      error: () => {
        this.visible = true;
        this.blockUI.stop();
      }
    });
  }

  pollBootstrapStatus(): void {
    const handleError = () => {
      this.visible = true;
      this.blockUI.stop();
      this.notificationService.show('Failed to bootstrap the system.', {
        type: 'error'
      });
    };
    this.bootstrapService
      .status()
      .pipe(
        this.pollService.poll(
          (statusReply) => statusReply.stage === BootstrapStageEnum.running,
          undefined,
          'Failed to bootstrap the system.'
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

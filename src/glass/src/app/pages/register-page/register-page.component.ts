import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { translate } from '~/app/i18n.helper';
import { GlassValidators } from '~/app/shared/forms/validators';
import {
  LocalNodeService,
  NodeStatus,
  StatusStageEnum
} from '~/app/shared/services/api/local.service';
import { NodesService } from '~/app/shared/services/api/nodes.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

const TOKEN_REGEXP = /^[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}$/i;

@Component({
  selector: 'glass-register-page',
  templateUrl: './register-page.component.html',
  styleUrls: ['./register-page.component.scss']
})
export class RegisterPageComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  joining = false;
  public formGroup: FormGroup;

  constructor(
    private formBuilder: FormBuilder,
    private nodesService: NodesService,
    private notificationService: NotificationService,
    private pollService: PollService,
    private router: Router,
    private localNodeService: LocalNodeService
  ) {
    this.formGroup = this.formBuilder.group({
      address: [null, [Validators.required, GlassValidators.hostAddress()]],
      token: [null, [Validators.required, Validators.pattern(TOKEN_REGEXP)]]
    });
  }

  ngOnInit(): void {
    this.blockUI.resetGlobal();
    this.localNodeService.status().subscribe((res: NodeStatus) => {
      if (res.node_stage === StatusStageEnum.joining) {
        this.joining = true;
        this.blockUI.start(
          translate(TEXT('Please wait, joining existing cluster in progress ...'))
        );
        this.pollJoiningStatus();
      }
    });
  }

  doJoin(): void {
    if (this.formGroup.pristine || this.formGroup.invalid) {
      return;
    }
    const values = this.formGroup.value;
    const handleError = () => {
      this.joining = false;
      this.blockUI.stop();
      this.notificationService.show(TEXT('Failed to join existing cluster.'), {
        type: 'error'
      });
    };
    this.joining = true;
    this.blockUI.start(translate(TEXT('Please wait, start joining existing cluster ...')));
    this.nodesService.join(values).subscribe({
      next: (success: boolean) => {
        if (success) {
          this.blockUI.update(
            translate(TEXT('Please wait, joining existing cluster in progress ...'))
          );
          this.pollJoiningStatus();
        } else {
          handleError();
        }
      },
      error: () => handleError()
    });
  }

  protected pollJoiningStatus(): void {
    const handleError = () => {
      this.joining = false;
      this.blockUI.stop();
      this.notificationService.show(TEXT('Failed to join existing cluster.'), {
        type: 'error'
      });
    };
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
              handleError();
              break;
            case StatusStageEnum.ready:
              this.joining = false;
              this.blockUI.stop();
              this.router.navigate(['/dashboard']);
              break;
          }
        },
        () => handleError()
      );
  }
}

import { Component, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ValidationErrors,
  ValidatorFn,
  Validators
} from '@angular/forms';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import validator from 'validator';

import { translate } from '~/app/i18n.helper';
import { NodesService } from '~/app/shared/services/api/nodes.service';
import { Status, StatusService, StatusStageEnum } from '~/app/shared/services/api/status.service';
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
    private statusService: StatusService
  ) {
    this.formGroup = this.formBuilder.group({
      address: [null, [Validators.required, this.addressValidator()]],
      token: [null, [Validators.required, Validators.pattern(TOKEN_REGEXP)]]
    });
  }

  ngOnInit(): void {
    this.blockUI.resetGlobal();
    this.statusService.status().subscribe((res: Status) => {
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
    this.statusService
      .status()
      .pipe(
        this.pollService.poll(
          (res: Status) => res.node_stage === StatusStageEnum.joining,
          undefined,
          TEXT('Failed to join existing cluster.')
        )
      )
      .subscribe(
        (res: Status) => {
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

  protected addressValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      if (_.isEmpty(control.value)) {
        return null;
      }
      const errResult = { address: true };
      const parts = control.value.split(':');
      if (parts.length === 2) {
        if (!validator.isPort(parts[1])) {
          return errResult;
        }
      }
      const valid =
        // eslint-disable-next-line @typescript-eslint/naming-convention
        validator.isIP(parts[0]) || validator.isFQDN(parts[0], { require_tld: false });
      return !valid ? errResult : null;
    };
  }
}

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
import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import * as _ from 'lodash';
import { Subscription } from 'rxjs';

import { InstallWizardContext } from '~/app/pages/install-wizard/models/install-wizard-context.type';
import { GlassValidators } from '~/app/shared/forms/validators';

@Component({
  selector: 'glass-ntp-step',
  templateUrl: './ntp-step.component.html',
  styleUrls: ['./ntp-step.component.scss']
})
export class NtpStepComponent implements OnInit, OnDestroy {
  @Input()
  context?: InstallWizardContext;

  public formGroup: FormGroup;
  public ntpDefault = 'pool.ntp.org';
  public useDefault = true;

  private subscription?: Subscription;

  constructor(private formBuilder: FormBuilder) {
    this.formGroup = this.formBuilder.group({
      ntpAddress: [null, [GlassValidators.hostAddress()]]
    });
    this.subscription = this.formGroup.valueChanges.subscribe(() => this.updateContext());
  }

  ngOnInit(): void {
    this.updateContext();
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  selectionChange(useDefault: boolean): void {
    this.useDefault = useDefault;
    this.updateContext();
  }

  private updateContext(): void {
    if (this.context) {
      _.merge(this.context.config, {
        ntpAddress: this.useDefault ? this.ntpDefault : this.formGroup.value.ntpAddress
      });
    }
  }
}

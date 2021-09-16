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
import { AfterViewInit, Component, Input, OnDestroy, ViewChild } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { Subscription } from 'rxjs';

import { InstallWizardContext } from '~/app/pages/install-wizard/models/install-wizard-context.type';
import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';
import { DeclarativeFormConfig } from '~/app/shared/models/declarative-form-config.type';

@Component({
  selector: 'glass-ntp-step',
  templateUrl: './ntp-step.component.html',
  styleUrls: ['./ntp-step.component.scss']
})
export class NtpStepComponent implements AfterViewInit, OnDestroy {
  @Input()
  context?: InstallWizardContext;

  @ViewChild(DeclarativeFormComponent, { static: true })
  form?: DeclarativeFormComponent;

  public config: DeclarativeFormConfig = {
    // eslint-disable-next-line max-len
    subtitle: TEXT(
      // eslint-disable-next-line max-len
      'Your cluster environment needs to have the time synchronized with a reliable time source. You do have two options in order to configure the time synchronization:'
    ),
    fields: [
      {
        name: 'useDefault',
        type: 'radio',
        label: TEXT('Use your own NTP host'),
        value: false,
        hint: TEXT(
          'If you do have your own NTP host configured on the network, please add it below.'
        )
      },
      {
        name: 'ntpAddress',
        type: 'text',
        label: TEXT('NTP host IP/FQDN'),
        groupClass: 'ml-4',
        hint: TEXT('The IP address or FQDN of the NTP host.'),
        validators: {
          patternType: 'hostAddress',
          requiredIf: {
            useDefault: { operator: 'falsy' }
          }
        }
      },
      {
        name: 'useDefault',
        type: 'radio',
        label: TEXT('Use an NTP host on the Internet'),
        value: true,
        hint: TEXT(
          // eslint-disable-next-line max-len
          'If you don not have your own NTP host configured, you can use an NTP server pool (pool.ntp.org) on the internet.<br><b>Please note:</b> This option requires access to the internet.'
        )
      }
    ]
  };

  private defaultNtpAddress = 'pool.ntp.org';
  private subscription?: Subscription;

  ngAfterViewInit(): void {
    if (this.context && this.form) {
      // Populate form fields with current values.
      const useDefault = [undefined, this.defaultNtpAddress].includes(
        this.context.config.ntpAddress
      );
      this.form.patchValues({
        useDefault,
        ntpAddress: useDefault ? '' : this.context.config.ntpAddress
      });
    }
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  get completed(): boolean {
    return this.form?.formGroup?.valid ?? false;
  }

  updateContext(): void {
    if (this.context && this.completed) {
      const values = this.form!.values;
      _.merge(this.context.config, {
        ntpAddress: values.useDefault ? this.defaultNtpAddress : values.ntpAddress
      });
    }
  }
}

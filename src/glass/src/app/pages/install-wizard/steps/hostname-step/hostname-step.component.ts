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
  selector: 'glass-hostname-step',
  templateUrl: './hostname-step.component.html',
  styleUrls: ['./hostname-step.component.scss']
})
export class HostnameStepComponent implements AfterViewInit, OnDestroy {
  @Input()
  context?: InstallWizardContext;

  @ViewChild(DeclarativeFormComponent, { static: true })
  form?: DeclarativeFormComponent;

  public config: DeclarativeFormConfig = {
    subtitle: TEXT('Please enter the hostname for this system.'),
    fields: [
      {
        name: 'hostname',
        type: 'text',
        label: TEXT('Hostname'),
        autofocus: true,
        validators: {
          required: true
        },
        hint: TEXT('The hostname is a single word that identifies the system to the network.')
      }
    ]
  };

  private subscription?: Subscription;

  ngAfterViewInit(): void {
    if (this.context && this.form) {
      // Populate form fields with current values.
      this.form.patchValues(this.context.config);
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
      _.merge(this.context.config, values);
    }
  }
}

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
  selector: 'glass-registration-step',
  templateUrl: './registration-step.component.html',
  styleUrls: ['./registration-step.component.scss']
})
export class RegistrationStepComponent implements AfterViewInit, OnDestroy {
  @Input()
  context?: InstallWizardContext;

  @ViewChild(DeclarativeFormComponent, { static: true })
  form?: DeclarativeFormComponent;

  public config: DeclarativeFormConfig = {
    hint: TEXT(
      'The token and address of the joining cluster can be found on the <em>Host</em> page of the UI.'
    ),
    fields: [
      {
        name: 'address',
        type: 'text',
        label: TEXT('Address'),
        validators: {
          required: true,
          patternType: 'hostAddress'
        },
        hint: TEXT('The IP address or FQDN of the main node.'),
        onPaste: this.onAddressPaste.bind(this)
      },
      {
        name: 'port',
        type: 'number',
        label: TEXT('Port'),
        value: 1337,
        validators: {
          required: true,
          min: 1,
          max: 65535
        }
      },
      {
        name: 'token',
        type: 'token',
        label: TEXT('Token'),
        validators: {
          required: true,
          pattern: /^[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}$/i
        },
        hint: TEXT('The security token to authorize at the main node.')
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

  /**
   * Process the pasted value. If it has the format '<address>:<port>',
   * then split the value and insert them into the corresponding form
   * fields.
   *
   * @param event The clipboard event.
   */
  private onAddressPaste(event: ClipboardEvent): void {
    // @ts-ignore
    const text = (event.clipboardData || window.clipboardData).getData('text');
    const matches = /^(.+):(\d+)$/.exec(text);
    if (matches && matches.length === 3) {
      event.preventDefault();
      this.form?.patchValues({ address: matches[1], port: matches[2] });
    }
  }
}

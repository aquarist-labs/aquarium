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
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { GlassValidators } from '~/app/shared/forms/validators';
import { OrchService } from '~/app/shared/services/api/orch.service';
import { NotificationService } from '~/app/shared/services/notification.service';

@Component({
  selector: 'glass-install-config-page',
  templateUrl: './install-config-page.component.html',
  styleUrls: ['./install-config-page.component.scss']
})
export class InstallConfigPageComponent implements OnInit {
  public formGroup: FormGroup;

  ntpDefault = 'pool.ntp.org';
  useDefault = false;

  constructor(
    private formBuilder: FormBuilder,
    private router: Router,
    private orchService: OrchService,
    private notificationService: NotificationService
  ) {
    this.formGroup = this.formBuilder.group({
      ntpAddress: [null, [Validators.required, GlassValidators.hostAddress()]]
    });
  }

  ngOnInit(): void {}

  selectionChange(selection: boolean): void {
    if (selection) {
      this.formGroup.reset();
    }
    this.useDefault = selection;
  }

  next(): void {
    let ntp = '';
    if (this.useDefault) {
      ntp = this.ntpDefault;
    } else {
      if (this.formGroup.pristine || this.formGroup.invalid) {
        return;
      }
      ntp = this.formGroup.value.ntpAddress;
    }

    this.orchService.setNtp(ntp).subscribe(
      () => {
        this.router.navigate(['/installer/create/bootstrap']);
      },
      (err) => {
        this.notificationService.show(err.message, {
          type: 'error'
        });
      }
    );
  }
}

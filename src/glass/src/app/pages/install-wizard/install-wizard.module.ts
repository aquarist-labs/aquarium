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
/* eslint-disable max-len */
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { TranslateModule } from '@ngx-translate/core';

import { InstallCreateWizardPageComponent } from '~/app/pages/install-wizard/install-create-wizard-page/install-create-wizard-page.component';
import { InstallJoinWizardPageComponent } from '~/app/pages/install-wizard/install-join-wizard-page/install-join-wizard-page.component';
import { HostnameStepComponent } from '~/app/pages/install-wizard/steps/hostname-step/hostname-step.component';
import { LocalDevicesStepComponent } from '~/app/pages/install-wizard/steps/local-devices-step/local-devices-step.component';
import { NtpStepComponent } from '~/app/pages/install-wizard/steps/ntp-step/ntp-step.component';
import { RegistrationStepComponent } from '~/app/pages/install-wizard/steps/registration-step/registration-step.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    InstallCreateWizardPageComponent,
    InstallJoinWizardPageComponent,
    NtpStepComponent,
    HostnameStepComponent,
    LocalDevicesStepComponent,
    RegistrationStepComponent
  ],
  imports: [
    CommonModule,
    FlexLayoutModule,
    NgbNavModule,
    RouterModule,
    SharedModule,
    TranslateModule.forChild()
  ],
  exports: [InstallCreateWizardPageComponent, InstallJoinWizardPageComponent]
})
export class InstallWizardModule {}

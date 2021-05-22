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
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

import { MaterialModule } from '~/app/material.modules';
import { InstallWizardPageComponent } from '~/app/pages/install-wizard-page/install-wizard-page.component';
import { HostDetailsStepComponent } from '~/app/pages/install-wizard-page/steps/host-details-step/host-details-step.component';
import { LocalDevicesStepComponent } from '~/app/pages/install-wizard-page/steps/local-devices-step/devices-step.component';
import { NetworkingStepComponent } from '~/app/pages/install-wizard-page/steps/networking-step/networking-step.component';
import { ServicesStepComponent } from '~/app/pages/install-wizard-page/steps/services-step/services-step.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    InstallWizardPageComponent,
    NetworkingStepComponent,
    HostDetailsStepComponent,
    ServicesStepComponent,
    LocalDevicesStepComponent
  ],
  imports: [
    CommonModule,
    FlexLayoutModule,
    MaterialModule,
    RouterModule,
    SharedModule,
    TranslateModule.forChild()
  ],
  exports: [InstallWizardPageComponent]
})
export class InstallWizardModule {}

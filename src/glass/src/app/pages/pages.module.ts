import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';

import { MaterialModule } from '~/app/material.modules';
import { BootstrapPageComponent } from '~/app/pages/bootstrap-page/bootstrap-page.component';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { DeploymentPageComponent } from '~/app/pages/deployment-page/deployment-page.component';
import { InstTypePageComponent } from '~/app/pages/inst-type-page/inst-type-page.component';
import { WelcomePageComponent } from '~/app/pages/welcome-page/welcome-page.component';

@NgModule({
  declarations: [
    BootstrapPageComponent,
    DashboardPageComponent,
    DeploymentPageComponent,
    InstTypePageComponent,
    WelcomePageComponent
  ],
  imports: [CommonModule, FlexLayoutModule, MaterialModule, RouterModule]
})
export class PagesModule {}

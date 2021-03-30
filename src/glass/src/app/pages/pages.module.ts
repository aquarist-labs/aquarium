import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

import { CoreModule } from '~/app/core/core.module';
import { MaterialModule } from '~/app/material.modules';
import { BootstrapPageComponent } from '~/app/pages/bootstrap-page/bootstrap-page.component';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { DeploymentPageComponent } from '~/app/pages/deployment-page/deployment-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { NotFoundPageComponent } from '~/app/pages/not-found-page/not-found-page.component';
import { RegisterPageComponent } from '~/app/pages/register-page/register-page.component';
import { ServicesPageComponent } from '~/app/pages/services-page/services-page.component';
import { WelcomePageComponent } from '~/app/pages/welcome-page/welcome-page.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    BootstrapPageComponent,
    DashboardPageComponent,
    DeploymentPageComponent,
    InstallModePageComponent,
    WelcomePageComponent,
    NotFoundPageComponent,
    RegisterPageComponent,
    ServicesPageComponent
  ],
  imports: [
    CommonModule,
    CoreModule,
    FlexLayoutModule,
    MaterialModule,
    RouterModule,
    SharedModule,
    TranslateModule.forChild()
  ]
})
export class PagesModule {}

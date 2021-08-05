import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { GridsterModule } from 'angular-gridster2';

import { CoreModule } from '~/app/core/core.module';
import { MaterialModule } from '~/app/material.modules';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { HostsPageComponent } from '~/app/pages/hosts-page/hosts-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { InstallWizardModule } from '~/app/pages/install-wizard/install-wizard.module';
import { LoginPageComponent } from '~/app/pages/login-page/login-page.component';
import { NotFoundPageComponent } from '~/app/pages/not-found-page/not-found-page.component';
import { UsersPageComponent } from '~/app/pages/users-page/users-page.component';
import { WelcomePageComponent } from '~/app/pages/welcome-page/welcome-page.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    DashboardPageComponent,
    InstallModePageComponent,
    WelcomePageComponent,
    NotFoundPageComponent,
    HostsPageComponent,
    LoginPageComponent,
    UsersPageComponent
  ],
  imports: [
    CommonModule,
    CoreModule,
    FlexLayoutModule,
    GridsterModule,
    MaterialModule,
    RouterModule,
    SharedModule,
    TranslateModule.forChild(),
    InstallWizardModule
  ]
})
export class PagesModule {}

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { TranslateModule } from '@ngx-translate/core';

import { CoreModule } from '~/app/core/core.module';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { HostsPageComponent } from '~/app/pages/hosts-page/hosts-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { InstallWelcomePageComponent } from '~/app/pages/install-welcome-page/install-welcome-page.component';
import { InstallWizardModule } from '~/app/pages/install-wizard/install-wizard.module';
import { LoginPageComponent } from '~/app/pages/login-page/login-page.component';
import { NetworkPageComponent } from '~/app/pages/network-page/network-page.component';
import { NotFoundPageComponent } from '~/app/pages/not-found-page/not-found-page.component';
import { UsersPageComponent } from '~/app/pages/users-page/users-page.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    DashboardPageComponent,
    InstallModePageComponent,
    NotFoundPageComponent,
    HostsPageComponent,
    LoginPageComponent,
    UsersPageComponent,
    InstallWelcomePageComponent,
    NetworkPageComponent
  ],
  imports: [
    CommonModule,
    CoreModule,
    FlexLayoutModule,
    NgbModule,
    RouterModule,
    SharedModule,
    TranslateModule.forChild(),
    InstallWizardModule
  ]
})
export class PagesModule {}

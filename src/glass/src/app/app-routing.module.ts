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
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { BlankLayoutComponent } from '~/app/core/layouts/blank-layout/blank-layout.component';
import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';
import { MainLayoutComponent } from '~/app/core/layouts/main-layout/main-layout.component';
import { BootstrapPageComponent } from '~/app/pages/bootstrap-page/bootstrap-page.component';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { DeploymentPageComponent } from '~/app/pages/deployment-page/deployment-page.component';
import { HostsPageComponent } from '~/app/pages/hosts-page/hosts-page.component';
import { InstallConfigPageComponent } from '~/app/pages/install-config-page/install-config-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { NotFoundPageComponent } from '~/app/pages/not-found-page/not-found-page.component';
import { RegisterPageComponent } from '~/app/pages/register-page/register-page.component';
import { ServicesPageComponent } from '~/app/pages/services-page/services-page.component';
import { WelcomePageComponent } from '~/app/pages/welcome-page/welcome-page.component';
import { StatusRouteGuardService } from '~/app/shared/services/status-route-guard.service';

const routes: Routes = [
  { path: '', redirectTo: 'installer', pathMatch: 'full' },
  {
    path: '',
    component: MainLayoutComponent,
    canActivateChild: [StatusRouteGuardService],
    children: [
      {
        path: 'dashboard',
        data: { breadcrumb: TEXT('Dashboard') },
        children: [
          { path: '', component: DashboardPageComponent },
          {
            path: 'services',
            component: ServicesPageComponent,
            data: { breadcrumb: TEXT('Services') }
          },
          { path: 'hosts', component: HostsPageComponent, data: { breadcrumb: TEXT('Hosts') } }
        ]
      }
    ]
  },
  {
    path: 'installer',
    component: InstallerLayoutComponent,
    canActivateChild: [StatusRouteGuardService],
    children: [
      { path: '', redirectTo: 'welcome', pathMatch: 'full' },
      { path: 'install-mode', component: InstallModePageComponent },
      { path: 'welcome', component: WelcomePageComponent },
      {
        path: 'create',
        children: [
          { path: 'config', component: InstallConfigPageComponent },
          { path: 'bootstrap', component: BootstrapPageComponent },
          { path: 'deployment', component: DeploymentPageComponent }
        ]
      },
      {
        path: 'join',
        children: [
          { path: 'register', component: RegisterPageComponent },
          { path: 'deployment', component: DeploymentPageComponent }
        ]
      }
    ]
  },
  {
    path: '',
    component: BlankLayoutComponent,
    children: [
      {
        path: '404',
        component: NotFoundPageComponent
      },
      { path: '**', redirectTo: '/404' }
    ]
  }
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, {
      useHash: true
    })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}

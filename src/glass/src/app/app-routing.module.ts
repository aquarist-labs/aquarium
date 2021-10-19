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
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { BlankLayoutComponent } from '~/app/core/layouts/blank-layout/blank-layout.component';
import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';
import { MainLayoutComponent } from '~/app/core/layouts/main-layout/main-layout.component';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { HostsPageComponent } from '~/app/pages/hosts-page/hosts-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { InstallWelcomePageComponent } from '~/app/pages/install-welcome-page/install-welcome-page.component';
import { InstallCreateWizardPageComponent } from '~/app/pages/install-wizard/install-create-wizard-page/install-create-wizard-page.component';
import { InstallJoinWizardPageComponent } from '~/app/pages/install-wizard/install-join-wizard-page/install-join-wizard-page.component';
import { LoginPageComponent } from '~/app/pages/login-page/login-page.component';
import { NetworkPageComponent } from '~/app/pages/network-page/network-page.component';
import { NotFoundPageComponent } from '~/app/pages/not-found-page/not-found-page.component';
import { UsersFormComponent } from '~/app/pages/users-page/users-form/users-form.component';
import { UsersPageComponent } from '~/app/pages/users-page/users-page.component';
import { AuthGuardService } from '~/app/shared/services/auth-guard.service';
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
        canActivate: [AuthGuardService],
        canActivateChild: [AuthGuardService],
        children: [
          { path: '', component: DashboardPageComponent },
          { path: 'hosts', component: HostsPageComponent, data: { breadcrumb: TEXT('Hosts') } },
          {
            path: 'network',
            component: NetworkPageComponent,
            data: { breadcrumb: TEXT('Network') }
          },
          {
            path: 'users',
            children: [
              { path: '', component: UsersPageComponent, data: { breadcrumb: TEXT('Users') } },
              {
                path: 'create',
                component: UsersFormComponent,
                data: { breadcrumb: TEXT('Create') }
              },
              {
                path: 'edit/:name',
                component: UsersFormComponent,
                data: { breadcrumb: TEXT('Edit') }
              }
            ],
            data: { breadcrumb: TEXT('Users') }
          }
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
      {
        path: 'welcome',
        component: InstallWelcomePageComponent,
        data: { breadcrumb: TEXT('Welcome') }
      },
      {
        path: 'install-mode',
        component: InstallModePageComponent,
        data: { breadcrumb: TEXT('Installer mode') }
      },
      {
        path: 'create',
        component: InstallCreateWizardPageComponent,
        data: { breadcrumb: TEXT('Create new cluster') }
      },
      {
        path: 'join',
        component: InstallJoinWizardPageComponent,
        data: { breadcrumb: TEXT('Join existing cluster') }
      }
    ]
  },
  {
    path: '',
    component: BlankLayoutComponent,
    children: [
      { path: 'login', component: LoginPageComponent },
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

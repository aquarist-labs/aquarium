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
import { Injectable, NgModule } from '@angular/core';
import { ActivatedRouteSnapshot, Resolve, Route, RouterModule, Routes } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { EMPTY } from 'rxjs';

import { BlankLayoutComponent } from '~/app/core/layouts/blank-layout/blank-layout.component';
import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';
import { MainLayoutComponent } from '~/app/core/layouts/main-layout/main-layout.component';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { EmptyPageComponent } from '~/app/pages/empty-page/empty-page.component';
import { HostsPageComponent } from '~/app/pages/hosts-page/hosts-page.component';
import { InstallBootstrapPageComponent } from '~/app/pages/install-bootstrap-page/install-bootstrap-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { InstallWelcomePageComponent } from '~/app/pages/install-welcome-page/install-welcome-page.component';
import { InstallCreateWizardPageComponent } from '~/app/pages/install-wizard/install-create-wizard-page/install-create-wizard-page.component';
import { InstallJoinWizardPageComponent } from '~/app/pages/install-wizard/install-join-wizard-page/install-join-wizard-page.component';
import { LoginPageComponent } from '~/app/pages/login-page/login-page.component';
import { NetworkFormComponent } from '~/app/pages/network-page/network-form/network-form.component';
import { NetworkPageComponent } from '~/app/pages/network-page/network-page.component';
import { NotFoundPageComponent } from '~/app/pages/not-found-page/not-found-page.component';
import { ShutdownPageComponent } from '~/app/pages/shutdown-page/shutdown-page.component';
import { StorageDevicesPageComponent } from '~/app/pages/storage-devices-page/storage-devices-page.component';
import { StorageSmartFormComponent } from '~/app/pages/storage-devices-page/storage-smart-form/storage-smart-form.component';
import { UsersFormComponent } from '~/app/pages/users-page/users-form/users-form.component';
import { UsersPageComponent } from '~/app/pages/users-page/users-page.component';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { Status, StatusService } from '~/app/shared/services/api/status.service';
import { AuthGuardService } from '~/app/shared/services/auth-guard.service';
import { DialogService } from '~/app/shared/services/dialog.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { StatusRouteGuardService } from '~/app/shared/services/status-route-guard.service';

@Injectable()
export class BubblesRedirectResolver implements Resolve<any> {
  constructor(
    private dialogService: DialogService,
    private notificationService: NotificationService,
    private statusService: StatusService
  ) {}

  resolve(route: ActivatedRouteSnapshot): any {
    const url = decodeURIComponent(route.paramMap.get('url')!);
    if (_.isString(url)) {
      this.statusService.status().subscribe((status: Status) => {
        const bubblesUrl: string | null = _.get(status, 'cluster.mgrmap.services.bubbles', null);
        if (!_.isString(bubblesUrl)) {
          this.notificationService.show(TEXT('Bubbles is not accessible.'), {
            type: 'error'
          });
        } else {
          this.dialogService.open(
            DialogComponent,
            (res: boolean) => {
              if (res) {
                window.open(`${_.trimEnd(bubblesUrl, '/')}/#${url}`, '_blank');
              }
            },
            {
              type: 'okCancel',
              icon: 'info',
              message: TEXT('This will redirect you to Bubbles.')
            }
          );
        }
      });
    }
    return EMPTY;
  }
}

const installerRoute: Route = {
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
      path: 'bootstrap',
      component: InstallBootstrapPageComponent,
      data: { breadcrumb: TEXT('Bootstrapping') }
    },
    {
      path: 'install-mode',
      component: InstallModePageComponent,
      data: { breadcrumb: TEXT('Installation mode') }
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
};

const dashboardRoute: Route = {
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
          data: { breadcrumb: TEXT('Network') },
          children: [
            { path: '', component: NetworkPageComponent },
            {
              path: 'edit/:name',
              component: NetworkFormComponent,
              data: { breadcrumb: TEXT('Edit') }
            }
          ]
        },
        {
          path: 'users',
          data: { breadcrumb: TEXT('Users') },
          children: [
            { path: '', component: UsersPageComponent },
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
          ]
        },
        {
          path: 'storage',
          data: { breadcrumb: TEXT('Storage') },
          children: [
            { path: '', component: StorageDevicesPageComponent },
            {
              path: 'smart/:path',
              component: StorageSmartFormComponent,
              data: { breadcrumb: TEXT('S.M.A.R.T.') }
            }
          ]
        }
      ]
    }
  ]
};

const glassRoutes: Routes = [
  { path: '', redirectTo: 'installer', pathMatch: 'full' },
  dashboardRoute,
  installerRoute,
  {
    path: '',
    component: BlankLayoutComponent,
    children: [
      { path: 'login', component: LoginPageComponent },
      { path: 'shutdown', component: ShutdownPageComponent },
      {
        path: 'bubblesRedirect/:url',
        resolve: {
          url: BubblesRedirectResolver
        },
        component: EmptyPageComponent
      },
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
    RouterModule.forRoot(glassRoutes, {
      useHash: true
    })
  ],
  exports: [RouterModule],
  providers: [BubblesRedirectResolver]
})
export class AppRoutingModule {}

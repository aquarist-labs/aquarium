import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { BlankLayoutComponent } from '~/app/core/layouts/blank-layout/blank-layout.component';
import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';
import { MainLayoutComponent } from '~/app/core/layouts/main-layout/main-layout.component';
import { BootstrapPageComponent } from '~/app/pages/bootstrap-page/bootstrap-page.component';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { DeploymentPageComponent } from '~/app/pages/deployment-page/deployment-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { NotFoundPageComponent } from '~/app/pages/not-found-page/not-found-page.component';
import { WelcomePageComponent } from '~/app/pages/welcome-page/welcome-page.component';
import { StatusRouteGuardService } from '~/app/shared/services/status-route-guard.service';

const routes: Routes = [
  { path: '', redirectTo: 'installer', pathMatch: 'full' },
  {
    path: '',
    component: MainLayoutComponent,
    canActivateChild: [StatusRouteGuardService],
    children: [{ path: 'dashboard', component: DashboardPageComponent }]
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
          { path: 'bootstrap', component: BootstrapPageComponent },
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

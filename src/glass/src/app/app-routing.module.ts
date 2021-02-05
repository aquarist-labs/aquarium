import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';
import { MainLayoutComponent } from '~/app/core/layouts/main-layout/main-layout.component';
import { BootstrapPageComponent } from '~/app/pages/bootstrap-page/bootstrap-page.component';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { DeploymentPageComponent } from '~/app/pages/deployment-page/deployment-page.component';
import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { WelcomePageComponent } from '~/app/pages/welcome-page/welcome-page.component';

const routes: Routes = [
  { path: '', redirectTo: 'installer', pathMatch: 'full' },
  {
    path: '',
    component: MainLayoutComponent,
    children: [{ path: 'dashboard', component: DashboardPageComponent }]
  },
  {
    path: 'installer',
    component: InstallerLayoutComponent,
    children: [
      { path: '', redirectTo: 'welcome', pathMatch: 'full' },
      { path: 'bootstrap', component: BootstrapPageComponent },
      { path: 'deployment', component: DeploymentPageComponent },
      { path: 'install-mode', component: InstallModePageComponent },
      { path: 'welcome', component: WelcomePageComponent }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}

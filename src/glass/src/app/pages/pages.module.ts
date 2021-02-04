import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';

import { MaterialModule } from '~/app/material.modules';
import { DashboardPageComponent } from '~/app/pages/dashboard-page/dashboard-page.component';
import { WelcomePageComponent } from '~/app/pages/welcome-page/welcome-page.component';

@NgModule({
  declarations: [DashboardPageComponent, WelcomePageComponent],
  imports: [CommonModule, FlexLayoutModule, MaterialModule, RouterModule]
})
export class PagesModule {}

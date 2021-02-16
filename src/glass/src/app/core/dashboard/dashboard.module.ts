/* eslint-disable max-len */
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';

import { CapacityDashboardWidgetComponent } from '~/app/core/dashboard/widgets/capacity-dashboard-widget/capacity-dashboard-widget.component';
import { HealthDashboardWidgetComponent } from '~/app/core/dashboard/widgets/health-dashboard-widget/health-dashboard-widget.component';
import { VolumesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/volumes-dashboard-widget/volumes-dashboard-widget.component';
import { MaterialModule } from '~/app/material.modules';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    CapacityDashboardWidgetComponent,
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent
  ],
  exports: [
    CapacityDashboardWidgetComponent,
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent
  ],
  imports: [CommonModule, FlexLayoutModule, MaterialModule, SharedModule]
})
export class DashboardModule {}

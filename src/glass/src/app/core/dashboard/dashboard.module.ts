/* eslint-disable max-len */
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';

import { CapacityDashboardWidgetComponent } from '~/app/core/dashboard/widgets/capacity-dashboard-widget/capacity-dashboard-widget.component';
import { DevicesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/devices-dashboard-widget/devices-dashboard-widget.component';
import { HealthDashboardWidgetComponent } from '~/app/core/dashboard/widgets/health-dashboard-widget/health-dashboard-widget.component';
import { MaterialModule } from '~/app/material.modules';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    CapacityDashboardWidgetComponent,
    DevicesDashboardWidgetComponent,
    HealthDashboardWidgetComponent
  ],
  exports: [
    CapacityDashboardWidgetComponent,
    DevicesDashboardWidgetComponent,
    HealthDashboardWidgetComponent
  ],
  imports: [CommonModule, FlexLayoutModule, MaterialModule, SharedModule]
})
export class DashboardModule {}

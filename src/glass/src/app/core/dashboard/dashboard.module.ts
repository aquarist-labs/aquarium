/* eslint-disable max-len */
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { NgxChartsModule } from '@swimlane/ngx-charts';

import { CapacityDashboardWidgetComponent } from '~/app/core/dashboard/widgets/capacity-dashboard-widget/capacity-dashboard-widget.component';
import { HealthDashboardWidgetComponent } from '~/app/core/dashboard/widgets/health-dashboard-widget/health-dashboard-widget.component';
import { HostsDashboardWidgetComponent } from '~/app/core/dashboard/widgets/hosts-dashboard-widget/hosts-dashboard-widget.component';
import { ServicesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/services-dashboard-widget/services-dashboard-widget.component';
import { SysInfoDashboardWidgetComponent } from '~/app/core/dashboard/widgets/sys-info-dashboard-widget/sys-info-dashboard-widget.component';
import { VolumesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/volumes-dashboard-widget/volumes-dashboard-widget.component';
import { MaterialModule } from '~/app/material.modules';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    CapacityDashboardWidgetComponent,
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    ServicesDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    HostsDashboardWidgetComponent
  ],
  exports: [
    CapacityDashboardWidgetComponent,
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    ServicesDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    HostsDashboardWidgetComponent
  ],
  imports: [
    CommonModule,
    FlexLayoutModule,
    MaterialModule,
    NgxChartsModule,
    SharedModule,
    RouterModule
  ]
})
export class DashboardModule {}

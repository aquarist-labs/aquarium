/* eslint-disable max-len */
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { NgxEchartsModule } from 'ngx-echarts';

import { DeviceUtilizationDashboardWidgetComponent } from '~/app/core/dashboard/widgets/device-utilization-dashboard-widget/device-utilization-dashboard-widget.component';
import { EventsDashboardWidgetComponent } from '~/app/core/dashboard/widgets/events-dashboard-widget/events-dashboard-widget.component';
import { HealthDashboardWidgetComponent } from '~/app/core/dashboard/widgets/health-dashboard-widget/health-dashboard-widget.component';
import { LoadDashboardWidgetComponent } from '~/app/core/dashboard/widgets/load-dashboard-widget/load-dashboard-widget.component';
import { MemoryDashboardWidgetComponent } from '~/app/core/dashboard/widgets/memory-dashboard-widget/memory-dashboard-widget.component';
import { SysInfoDashboardWidgetComponent } from '~/app/core/dashboard/widgets/sys-info-dashboard-widget/sys-info-dashboard-widget.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    EventsDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    MemoryDashboardWidgetComponent,
    LoadDashboardWidgetComponent,
    DeviceUtilizationDashboardWidgetComponent
  ],
  exports: [
    EventsDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    MemoryDashboardWidgetComponent,
    LoadDashboardWidgetComponent,
    DeviceUtilizationDashboardWidgetComponent
  ],
  imports: [
    CommonModule,
    FlexLayoutModule,
    NgxEchartsModule.forRoot({ echarts: () => import('echarts') }),
    SharedModule,
    RouterModule,
    TranslateModule.forChild()
  ]
})
export class DashboardModule {}

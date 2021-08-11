/* eslint-disable max-len */
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { NgxChartsModule } from '@swimlane/ngx-charts';

import { HealthDashboardWidgetComponent } from '~/app/core/dashboard/widgets/health-dashboard-widget/health-dashboard-widget.component';
import { HostsDashboardWidgetComponent } from '~/app/core/dashboard/widgets/hosts-dashboard-widget/hosts-dashboard-widget.component';
import { PerformanceDashboardWidgetComponent } from '~/app/core/dashboard/widgets/performance-dashboard-widget/performance-dashboard-widget.component';
import { SysInfoDashboardWidgetComponent } from '~/app/core/dashboard/widgets/sys-info-dashboard-widget/sys-info-dashboard-widget.component';
import { VolumesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/volumes-dashboard-widget/volumes-dashboard-widget.component';
import { MaterialModule } from '~/app/material.modules';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    HostsDashboardWidgetComponent,
    PerformanceDashboardWidgetComponent
  ],
  exports: [
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    HostsDashboardWidgetComponent,
    PerformanceDashboardWidgetComponent
  ],
  imports: [
    CommonModule,
    FlexLayoutModule,
    MaterialModule,
    NgxChartsModule,
    SharedModule,
    RouterModule,
    TranslateModule.forChild()
  ]
})
export class DashboardModule {}

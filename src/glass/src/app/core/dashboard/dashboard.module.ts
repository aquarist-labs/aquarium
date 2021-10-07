/* eslint-disable max-len */
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { NgxEchartsModule } from 'ngx-echarts';

import { EventsDashboardWidgetComponent } from '~/app/core/dashboard/widgets/events-dashboard-widget/events-dashboard-widget.component';
import { HealthDashboardWidgetComponent } from '~/app/core/dashboard/widgets/health-dashboard-widget/health-dashboard-widget.component';
import { PerformanceDashboardWidgetComponent } from '~/app/core/dashboard/widgets/performance-dashboard-widget/performance-dashboard-widget.component';
import { SysInfoDashboardWidgetComponent } from '~/app/core/dashboard/widgets/sys-info-dashboard-widget/sys-info-dashboard-widget.component';
import { VolumesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/volumes-dashboard-widget/volumes-dashboard-widget.component';
import { SharedModule } from '~/app/shared/shared.module';

@NgModule({
  declarations: [
    EventsDashboardWidgetComponent,
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    PerformanceDashboardWidgetComponent
  ],
  exports: [
    EventsDashboardWidgetComponent,
    VolumesDashboardWidgetComponent,
    HealthDashboardWidgetComponent,
    SysInfoDashboardWidgetComponent,
    PerformanceDashboardWidgetComponent
  ],
  imports: [
    CommonModule,
    FlexLayoutModule,
    NgxChartsModule,
    NgxEchartsModule.forRoot({ echarts: () => import('echarts') }),
    SharedModule,
    RouterModule,
    TranslateModule.forChild()
  ]
})
export class DashboardModule {}

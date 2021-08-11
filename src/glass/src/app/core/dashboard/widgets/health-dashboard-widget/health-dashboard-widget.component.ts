import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';

import { translate } from '~/app/i18n.helper';
import { WidgetHealthStatus } from '~/app/shared/components/widget/widget.component';
import { Status, StatusService } from '~/app/shared/services/api/status.service';

type HealthMetaObj = { boxShadow: WidgetHealthStatus; statusText: string; setLocalVar: () => void };

@Component({
  selector: 'glass-health-dashboard-widget',
  templateUrl: './health-dashboard-widget.component.html',
  styleUrls: ['./health-dashboard-widget.component.scss']
})
export class HealthDashboardWidgetComponent {
  public isError = false;
  public isWarn = false;
  public isOkay = false;
  public hasStatus = false;
  public statusText = '';

  private healthMetaObjs: { [status: string]: HealthMetaObj } = {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    health_ok: {
      boxShadow: WidgetHealthStatus.success,
      statusText: translate(TEXT('OK')),
      setLocalVar: () => (this.isOkay = true)
    },
    // eslint-disable-next-line @typescript-eslint/naming-convention
    health_warn: {
      boxShadow: WidgetHealthStatus.warning,
      statusText: translate(TEXT('Warning')),
      setLocalVar: () => (this.isWarn = true)
    },
    // eslint-disable-next-line @typescript-eslint/naming-convention
    health_err: {
      boxShadow: WidgetHealthStatus.error,
      statusText: translate(TEXT('Error')),
      setLocalVar: () => (this.isError = true)
    },
    waitingForStatus: {
      boxShadow: WidgetHealthStatus.info,
      statusText: '',
      setLocalVar: () => (this.hasStatus = false)
    }
  };

  public constructor(private statusService: StatusService) {}

  setHealthStatus(status: Status) {
    this.isError = this.isWarn = this.isOkay = false;
    this.hasStatus = true;
    const healthObj = this.getHealthObj(status);
    this.statusText = healthObj.statusText;
    healthObj.setLocalVar();
  }

  loadData(): Observable<Status> {
    return this.statusService.status();
  }

  setHealthStatusIndicator(status: Status): WidgetHealthStatus {
    return this.getHealthObj(status).boxShadow;
  }

  private getHealthObj(status: Status): HealthMetaObj {
    return this.healthMetaObjs[
      !status.cluster ? 'waitingForStatus' : status.cluster.health.status.toLowerCase()
    ];
  }
}

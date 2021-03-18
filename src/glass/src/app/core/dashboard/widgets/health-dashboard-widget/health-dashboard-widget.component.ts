import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';

import { translate } from '~/app/i18n.helper';
import { Status, StatusService } from '~/app/shared/services/api/status.service';

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

  public constructor(private statusService: StatusService) {}

  setHealthStatus(status: Status) {
    this.isError = this.isWarn = this.isOkay = false;
    this.hasStatus = false;

    if (!status.cluster) {
      return;
    }

    this.hasStatus = true;
    switch (status.cluster.health.status.toLowerCase()) {
      case 'health_ok':
        this.isOkay = true;
        this.statusText = translate(TEXT('OK'));
        break;
      case 'health_warn':
        this.isWarn = true;
        this.statusText = translate(TEXT('Warning'));
        break;
      case 'health_err':
        this.isError = true;
        this.statusText = translate(TEXT('Error'));
        break;
      default:
        this.hasStatus = false;
        break;
    }
  }

  loadData(): Observable<Status> {
    return this.statusService.status();
  }
}

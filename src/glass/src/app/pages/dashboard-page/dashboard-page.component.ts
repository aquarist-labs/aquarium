import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import {
  CompactType,
  DisplayGrid,
  GridsterConfig,
  GridsterItem,
  GridType
} from 'angular-gridster2';
import * as _ from 'lodash';

import { DashboardWidgetConfig } from '~/app/shared/models/dashboard-widget.model';
import { LocalStorageService } from '~/app/shared/services/local-storage.service';

@Component({
  selector: 'glass-dashboard-page',
  templateUrl: './dashboard-page.component.html',
  styleUrls: ['./dashboard-page.component.scss']
})
export class DashboardPageComponent {
  gridsterConfig: GridsterConfig = {
    setGridSize: true,
    gridType: GridType.Fixed,
    compactType: CompactType.CompactLeftAndUp,
    margin: 12,
    outerMargin: false,
    outerMarginTop: null,
    outerMarginRight: null,
    outerMarginBottom: null,
    outerMarginLeft: null,
    useTransformPositioning: true,
    mobileBreakpoint: 640,
    minCols: 12,
    minRows: 10,
    fixedColWidth: 48,
    fixedRowHeight: 48,
    keepFixedHeightInMobile: true,
    keepFixedWidthInMobile: false,
    scrollSensitivity: 10,
    scrollSpeed: 20,
    enableEmptyCellClick: false,
    enableEmptyCellContextMenu: false,
    enableEmptyCellDrop: false,
    enableEmptyCellDrag: false,
    enableOccupiedCellDrop: false,
    draggable: {
      enabled: true
    },
    resizable: {
      enabled: true
    },
    swap: true,
    swapWhileDragging: true,
    pushItems: true,
    disablePushOnDrag: false,
    disablePushOnResize: false,
    pushDirections: { north: true, east: true, south: true, west: true },
    pushResizeItems: false,
    displayGrid: DisplayGrid.None,
    disableWindowResize: false,
    disableWarnings: true,
    scrollToNewItems: false,
    itemChangeCallback: (): void => {
      this.saveSettings();
    }
  };
  gridsterItems: Array<GridsterItem> = [];

  // New dashboard widgets must be added here. Don't forget to enhance
  // the template to render the new widget.
  readonly widgets: DashboardWidgetConfig[] = [
    {
      id: 'health',
      title: TEXT('Health'),
      cols: 3,
      rows: 2,
      enabledByDefault: true
    },
    {
      id: 'capacity',
      title: TEXT('Allocated Storage'),
      cols: 6,
      rows: 4,
      enabledByDefault: true
    },
    {
      id: 'performance',
      title: TEXT('Performance'),
      cols: 6,
      rows: 4,
      enabledByDefault: true
    },
    {
      id: 'services',
      title: TEXT('Services'),
      cols: 6,
      rows: 4,
      enabledByDefault: false
    },
    {
      id: 'volumes',
      title: TEXT('Volumes'),
      cols: 6,
      rows: 4,
      enabledByDefault: false
    },
    {
      id: 'sysInfo',
      title: TEXT('System Information'),
      cols: 7,
      rows: 9,
      enabledByDefault: false
    },
    {
      id: 'hosts',
      title: TEXT('Hosts'),
      cols: 6,
      rows: 4,
      enabledByDefault: false
    },
    {
      id: 'services-capacity',
      title: TEXT('Services Capacity'),
      cols: 6,
      rows: 4,
      enabledByDefault: true
    },
    {
      id: 'services-utilization',
      title: TEXT('Services Utilization'),
      cols: 6,
      rows: 4,
      enabledByDefault: true
    }
  ];

  constructor(private localStorageService: LocalStorageService) {
    this.loadSettings();
  }

  onToggleWidget(id: string) {
    if (this.enabled.includes(id)) {
      this.removeWidget(id);
    } else {
      this.addWidget(id);
    }
    this.saveSettings();
  }

  get enabled(): Array<string> {
    return _.map(this.gridsterItems, 'type');
  }

  loadSettings(): void {
    const value = this.localStorageService.get('dashboard_widgets');
    if (_.isString(value)) {
      this.gridsterItems = JSON.parse(value);
    }
    // If no widgets are configured, then show the default ones.
    if (!this.gridsterItems.length) {
      _.forEach(
        _.filter(this.widgets, ['enabledByDefault', true]),
        (widget: DashboardWidgetConfig) => {
          // Add ALL widgets with position (0,0), the grid will rearrange
          // them automatically.
          this.gridsterItems.push({
            cols: widget.cols,
            rows: widget.rows,
            x: 0,
            y: 0,
            type: widget.id
          });
        }
      );
    }
  }

  saveSettings(): void {
    this.localStorageService.set('dashboard_widgets', JSON.stringify(this.gridsterItems));
  }

  private addWidget(id: string): void {
    const widget = _.find(this.widgets, ['id', id]);
    if (widget) {
      const gridsterItem: GridsterItem = {
        cols: widget.cols,
        rows: widget.rows,
        x: 0,
        y: 0,
        type: id
      };
      // Ask the grid for the next possible widget position.
      const getNextPossiblePosition = this.gridsterConfig.api?.getNextPossiblePosition;
      if (_.isFunction(getNextPossiblePosition) && getNextPossiblePosition(gridsterItem)) {
        this.gridsterItems.push(gridsterItem);
      }
    }
  }

  private removeWidget(id: string): void {
    this.gridsterItems = _.reject(this.gridsterItems, ['type', id]);
  }
}

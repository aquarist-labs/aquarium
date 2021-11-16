import { Component, Input } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

export enum PageStatus {
  none = 0,
  ready = 1,
  loading = 2,
  loadingError = 3
}

@Component({
  selector: 'glass-content-page',
  templateUrl: './content-page.component.html',
  styleUrls: ['./content-page.component.scss']
})
export class ContentPageComponent {
  @Input()
  pageStatus: PageStatus = PageStatus.ready;

  @Input()
  loadingErrorText? = TEXT('Failed to load data.');
}

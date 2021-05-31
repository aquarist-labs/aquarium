/* eslint-disable max-len */
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { AllocationsDashboardWidgetComponent } from '~/app/core/dashboard/widgets/allocations-dashboard-widget/allocations-dashboard-widget.component';

describe('AllocationsDashboardWidgetComponent', () => {
  let component: AllocationsDashboardWidgetComponent;
  let fixture: ComponentFixture<AllocationsDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        DashboardModule,
        HttpClientTestingModule,
        TranslateModule.forRoot(),
        BrowserAnimationsModule
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AllocationsDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

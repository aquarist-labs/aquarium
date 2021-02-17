import { Component, NgModule } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { ChooseDevicesModalComponent } from '~/app/pages/deployment-page/choose-devices-modal/choose-devices-modal.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('ChooseDevicesModalComponent', () => {
  let dialog: MatDialog;

  let component: ComponentFixture<EmptyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DialogTestModule]
    }).compileComponents();

    dialog = TestBed.get(MatDialog);
    component = TestBed.createComponent(EmptyComponent);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should open', () => {
    dialog.open(ChooseDevicesModalComponent);
  });
});

@Component({
  template: ''
})
class EmptyComponent {}

@NgModule({
  imports: [MatDialogModule, NoopAnimationsModule, PagesModule],
  exports: [EmptyComponent],
  declarations: [EmptyComponent],
  entryComponents: [ChooseDevicesModalComponent]
})
class DialogTestModule {}

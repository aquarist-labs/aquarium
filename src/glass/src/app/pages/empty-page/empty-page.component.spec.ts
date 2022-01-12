import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmptyPageComponent } from '~/app/pages/empty-page/empty-page.component';

describe('EmptyPageComponent', () => {
  let component: EmptyPageComponent;
  let fixture: ComponentFixture<EmptyPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [EmptyPageComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EmptyPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

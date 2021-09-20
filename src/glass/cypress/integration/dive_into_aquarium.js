describe('Dive into Aquarium', () => {
  it('Visit the first tank', () => {
    cy.visit('/');
    cy.contains('Create new cluster').click();
    cy.contains('Start');
    cy.contains('Networking');
    cy.contains('Time');
    cy.contains('Devices');
    cy.contains('Installation');
    cy.contains('Finish');
    cy.contains('Next');
    cy.contains('Next').click();
    cy.contains('Hostname');
    cy.contains('div', 'Hostname').find('input').type('foohost{enter}');
    cy.get('button:contains("Next")').filter(':visible').click();
    cy.contains('Use an NTP host on the Internet').click();
    cy.get('button:contains("Next")').filter(':visible').click();
    cy.get('button:contains("Next")').filter(':visible').click();
    cy.get('button:contains("Install")').filter(':visible').click();
  });
});

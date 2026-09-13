(function (root) {
  'use strict';

  const option = (name, returns, projectionPeriod) => ({name, returns, projectionPeriod});
  root.INVESTMENT_RETURNS = Object.freeze({
    asAt: '31 July 2026',
    checked: '13 September 2026',
    sourceName: 'Cbus Super published crediting rates',
    sourceUrls: {
      accumulation: 'https://www.cbussuper.com.au/super/my-investment-options',
      pension: 'https://www.cbussuper.com.au/retirement/my-retirement-investment-options/fully-retired-investment-options'
    },
    note: 'Historical crediting rates after investment fees, costs, transaction costs and investment-related tax where applicable. Past performance is not a forecast.',
    accumulation: [
      option('Growth (MySuper)', {oneYear: 8.30, threeYears: 8.93, fiveYears: 6.37, tenYears: 7.91}, 'tenYears'),
      option('High Growth', {oneYear: 8.60, threeYears: 10.35, fiveYears: 7.48, tenYears: 9.51}, 'tenYears'),
      option('Growth Plus', {oneYear: 8.54, threeYears: 9.66}, 'threeYears'),
      option('Indexed Diversified', {oneYear: 7.76, threeYears: 10.26}, 'threeYears'),
      option('Conservative Growth', {oneYear: 6.53, threeYears: 7.26, fiveYears: 4.79}, 'fiveYears'),
      option('Conservative', {oneYear: 4.82, threeYears: 5.56, fiveYears: 3.33, tenYears: 4.30}, 'tenYears'),
      option('Overseas Shares', {oneYear: 8.26, threeYears: 13.99}, 'threeYears'),
      option('Australian Shares', {oneYear: 4.82, threeYears: 8.97}, 'threeYears'),
      option('Property', {oneYear: 13.03, threeYears: 5.20}, 'threeYears'),
      option('Diversified Fixed Interest', {oneYear: 3.26, threeYears: 4.56}, 'threeYears'),
      option('Cash', {oneYear: 3.72, threeYears: 3.99, fiveYears: 3.05, tenYears: 2.06}, 'tenYears')
    ],
    pension: [
      option('Conservative Growth (default)', {oneYear: 6.80, threeYears: 7.83, fiveYears: 5.29, sevenYears: 6.06, tenYears: 6.84}, 'tenYears'),
      option('High Growth', {oneYear: 9.19, threeYears: 11.22, fiveYears: 8.24, sevenYears: 9.68, tenYears: 10.50}, 'tenYears'),
      option('Growth Plus', {oneYear: 8.84, threeYears: 10.31}, 'threeYears'),
      option('Growth', {oneYear: 8.46, threeYears: 9.62, fiveYears: 6.95, sevenYears: 7.92, tenYears: 8.73}, 'tenYears'),
      option('Indexed Diversified', {oneYear: 8.90, threeYears: 11.61}, 'threeYears'),
      option('Conservative', {oneYear: 5.08, threeYears: 6.09, fiveYears: 3.57, sevenYears: 4.03, tenYears: 4.75}, 'tenYears'),
      option('Overseas Shares', {oneYear: 9.12, threeYears: 15.24}, 'threeYears'),
      option('Australian Shares', {oneYear: 5.49, threeYears: 9.98}, 'threeYears'),
      option('Property', {oneYear: 14.70, threeYears: 5.61}, 'threeYears'),
      option('Diversified Fixed Interest', {oneYear: 3.81, threeYears: 5.36}, 'threeYears'),
      option('Cash', {oneYear: 4.34, threeYears: 4.60, fiveYears: 3.52, sevenYears: 2.64, tenYears: 2.44}, 'tenYears')
    ]
  });
})(typeof globalThis === 'object' ? globalThis : window);

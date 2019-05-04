//*************
//The basics
//*************
var substringMatcher = function(strs) {
  return function findMatches(q, cb) {
    var matches, substringRegex;

    // an array that will be populated with substring matches
    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    $.each(strs, function(i, str) {
      if (substrRegex.test(str)) {
        matches.push(str);
      }
    });

    cb(matches);
  };
};

var reg_numbers = ['123456789', '321654987'];;
var breeders = ['Example Breeder 1', 'Example Breeder 2', 'Example Breeder 3', 'Example Breeder 4', 'Example Breeder 5'];;
var breeds = ['Australorp', 'Delaware', 'New Hampshire', 'Buckeye'];;

$('#reg_numbers .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'reg_numbers',
  source: substringMatcher(reg_numbers)
});

$('#breeders .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'breeders',
  source: substringMatcher(breeders)
});

$('#breeds .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'breeds',
  source: substringMatcher(breeds)
});
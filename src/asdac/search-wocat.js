
document.addEventListener("DOMContentLoaded", () => {

  const endpoint = "https://explorer.wocat.net/api/search";

  const resultsContainer = document.getElementById("search-results");
  const countrySelect = document.getElementById("country-filter");

  // African countries
  const africanCountries = [
    "Algeria",
    "Angola",
    "Benin",
    "Botswana",
    "Burkina Faso",
    "Burundi",
    "Cabo Verde",
    "Cameroon",
    "Central African Republic",
    "Chad",
    "Comoros",
    "Democratic Republic of the Congo",
    "Republic of the Congo",
    "Côte d'Ivoire",
    "Djibouti",
    "Egypt",
    "Equatorial Guinea",
    "Eritrea",
    "Eswatini",
    "Ethiopia",
    "Gabon",
    "Gambia",
    "Ghana",
    "Guinea",
    "Guinea-Bissau",
    "Kenya",
    "Lesotho",
    "Liberia",
    "Libya",
    "Madagascar",
    "Malawi",
    "Mali",
    "Mauritania",
    "Mauritius",
    "Morocco",
    "Mozambique",
    "Namibia",
    "Niger",
    "Nigeria",
    "Rwanda",
    "Sao Tome and Principe",
    "Senegal",
    "Seychelles",
    "Sierra Leone",
    "Somalia",
    "South Africa",
    "South Sudan",
    "Sudan",
    "Tanzania",
    "Togo",
    "Tunisia",
    "Uganda",
    "Zambia",
    "Zimbabwe"
  ];

  // Populate country dropdown
  africanCountries.forEach(country => {
    const option = document.createElement("option");
    option.value = country;
    option.textContent = country;
    countrySelect.appendChild(option);
  });

  // Load results
  async function loadResults() {

    resultsContainer.textContent = "Loading results...";

    const selectedCountry = countrySelect.value;

    const requestBody = {
      dashboard: null,
      query: {
        sort: [
          {
            _score: {
              order: "desc"
            }
          }
        ],
        from: 0,
        size: 10,
        _source: [
          "Name",
          "short_description",
          "slm_link",
          "Image",
          "https://qcat.wocat.net/",
          "slm_type",
          "compilers",
          "Name of institution",
          "date_documentation",
          "Country",
          "id",
          "repo"
        ],
        ...(selectedCountry && {
          "query": {
            "bool": {
                "filter": {
                    "terms": {
                        "Country.keyword": [
                            selectedCountry
                        ]
                    }
                }
            }
        }
        })
      }
    };

    try {

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
          // "Authorization": "Bearer YOUR_TOKEN"
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();

      const hits = data.hits?.hits || [];
      const total = data.hits?.total?.value ?? hits.length;

      resultsContainer.replaceChildren();

      const count = document.createElement("p");
      count.textContent = `${total} results found`;
      resultsContainer.appendChild(count);

      if (hits.length === 0) {
        const message = document.createElement("p");
        message.textContent = "No results found.";
        resultsContainer.appendChild(message);
        return;
      }

      hits.forEach(hit => {

        const source = hit._source || {};

        const card = document.createElement("div");
        card.className = "card mb-3";

        const cardBody = document.createElement("div");
        cardBody.className = "card-body";

        const heading = document.createElement("h3");
        heading.className = "card-title";

        const link = document.createElement("a");
        link.href = source.slm_link || "#";
        link.textContent = source.Name || "Untitled";

        heading.appendChild(link);

        const description = document.createElement("p");
        description.className = "card-text";
        description.textContent =
          source.short_description || "";

        cardBody.appendChild(heading);
        cardBody.appendChild(description);

        card.appendChild(cardBody);

        resultsContainer.appendChild(card);
      });

    } catch (error) {

      console.error("Elasticsearch error:", error);

      resultsContainer.textContent =
        "An error occurred while retrieving results.";

    }
  }

  // Reload results when country changes
  countrySelect.addEventListener("change", loadResults);

  // Initial load
  loadResults();

});
